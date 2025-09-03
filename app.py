import os
import uuid
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from database import get_db_connection, init_app

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'html'}

init_app(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_file_consistency(file_path):
    return os.path.exists(os.path.join(app.root_path, file_path))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_page')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        doc_id = request.form.get('doc_id')
        metadata_str = request.form.get('metadata')
        change_description = request.form.get('change_description')

        try:
            metadata = json.loads(metadata_str)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON format for metadata'}), 400

        html_files = request.files.getlist('html_files')
        html_paths = []
        for html_file in html_files:
            if html_file and allowed_file(html_file.filename):
                html_filename = str(uuid.uuid4()) + os.path.splitext(html_file.filename)[1]
                html_path = os.path.join(app.config['UPLOAD_FOLDER'], html_filename)
                html_file.save(html_path)
                html_paths.append(html_path)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM documents WHERE doc_id = ?', (doc_id,))
        document = cursor.fetchone()

        if document:
            # Update existing document
            document_id = document['id']
            new_version = document['latest_version'] + 1

            existing_metadata = json.loads(document['metadata'])
            existing_metadata.update(metadata)
            new_metadata_str = json.dumps(existing_metadata)

            cursor.execute('UPDATE documents SET latest_version = ?, metadata = ? WHERE id = ?', (new_version, new_metadata_str, document_id))
            cursor.execute(
                'INSERT INTO versions (document_id, version, change_description, file_path) VALUES (?, ?, ?, ?)',
                (document_id, new_version, change_description, file_path)
            )
            version_id = cursor.lastrowid
            for html_path in html_paths:
                cursor.execute('INSERT INTO html_documents (version_id, file_path) VALUES (?, ?)', (version_id, html_path))
        else:
            # Create new document
            cursor.execute('INSERT INTO documents (doc_id, metadata) VALUES (?, ?)', (doc_id, json.dumps(metadata)))
            document_id = cursor.lastrowid
            cursor.execute(
                'INSERT INTO versions (document_id, version, change_description, file_path) VALUES (?, ?, ?, ?)',
                (document_id, 1, change_description, file_path)
            )
            version_id = cursor.lastrowid
            for html_path in html_paths:
                cursor.execute('INSERT INTO html_documents (version_id, file_path) VALUES (?, ?)', (version_id, html_path))

        conn.commit()

        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/documents')
def get_documents():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM documents ORDER BY id DESC')
    documents = cursor.fetchall()

    results = []
    for doc in documents:
        doc_dict = dict(doc)
        doc_dict['metadata'] = json.loads(doc_dict['metadata'])
        cursor.execute('SELECT * FROM versions WHERE document_id = ? ORDER BY version DESC', (doc['id'],))
        versions = cursor.fetchall()
        versions_list = []
        for v in versions:
            v_dict = dict(v)
            v_dict['file_consistent'] = check_file_consistency(v_dict['file_path'])
            cursor.execute('SELECT file_path FROM html_documents WHERE version_id = ?', (v['id'],))
            html_docs = cursor.fetchall()
            v_dict['html_paths'] = []
            for hp in html_docs:
                html_path_str = hp['file_path']
                v_dict['html_paths'].append({
                    'path': html_path_str,
                    'consistent': check_file_consistency(html_path_str)
                })
            versions_list.append(v_dict)
        doc_dict['versions'] = versions_list
        results.append(doc_dict)

    return jsonify(results)


@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor()

    # Search in documents table
    cursor.execute("SELECT * FROM documents WHERE metadata LIKE ?", (f'%{query}%',))
    documents = cursor.fetchall()

    # Search in versions table
    cursor.execute("SELECT document_id FROM versions WHERE change_description LIKE ?", (f'%{query}%',))
    version_doc_ids = [row['document_id'] for row in cursor.fetchall()]

    # Combine results
    doc_ids = set([doc['id'] for doc in documents])
    doc_ids.update(version_doc_ids)

    results = []
    for doc_id in doc_ids:
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        doc = cursor.fetchone()
        if doc:
            doc_dict = dict(doc)
            doc_dict['metadata'] = json.loads(doc_dict['metadata'])
            cursor.execute('SELECT * FROM versions WHERE document_id = ? ORDER BY version DESC', (doc['id'],))
            versions = cursor.fetchall()
            versions_list = []
            for v in versions:
                v_dict = dict(v)
                v_dict['file_consistent'] = check_file_consistency(v_dict['file_path'])
                cursor.execute('SELECT file_path FROM html_documents WHERE version_id = ?', (v['id'],))
                html_docs = cursor.fetchall()
                v_dict['html_paths'] = []
                for hp in html_docs:
                    html_path_str = hp['file_path']
                    v_dict['html_paths'].append({
                        'path': html_path_str,
                        'consistent': check_file_consistency(html_path_str)
                    })
                versions_list.append(v_dict)
            doc_dict['versions'] = versions_list
            results.append(doc_dict)

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)



