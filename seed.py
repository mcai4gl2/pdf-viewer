import sqlite3
import json

DATABASE_NAME = 'pdf_browser.db'

def seed_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute('DELETE FROM documents')
    cursor.execute('DELETE FROM versions')
    cursor.execute('DELETE FROM html_documents')

    # Document 1
    doc1_metadata = {'name': 'Document A', 'author': 'Author 1', 'year': 2023}
    cursor.execute('INSERT INTO documents (doc_id, metadata) VALUES (?, ?)', ('doc-a', json.dumps(doc1_metadata)))
    doc1_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO versions (document_id, version, change_description, file_path) VALUES (?, ?, ?, ?)',
        (doc1_id, 1, 'Initial version', 'uploads/doc-a-v1.pdf')
    )
    version1_id = cursor.lastrowid
    cursor.execute('INSERT INTO html_documents (version_id, file_path) VALUES (?, ?)', (version1_id, 'uploads/doc-a-v1-html1.html'))
    cursor.execute('INSERT INTO html_documents (version_id, file_path) VALUES (?, ?)', (version1_id, 'uploads/doc-a-v1-html2.html'))

    # Document 2
    doc2_metadata = {'name': 'Document B', 'category': 'Category X', 'status': 'draft'}
    cursor.execute('INSERT INTO documents (doc_id, metadata) VALUES (?, ?)', ('doc-b', json.dumps(doc2_metadata)))
    doc2_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO versions (document_id, version, change_description, file_path) VALUES (?, ?, ?, ?)',
        (doc2_id, 1, 'First version', 'uploads/doc-b-v1.pdf')
    )
    version2_id = cursor.lastrowid
    cursor.execute('INSERT INTO html_documents (version_id, file_path) VALUES (?, ?)', (version2_id, 'uploads/doc-b-v1-html1.html'))

    cursor.execute('UPDATE documents SET latest_version = ? WHERE id = ?', (2, doc2_id))
    doc2_metadata['status'] = 'published'
    cursor.execute('UPDATE documents SET metadata = ? WHERE id = ?', (json.dumps(doc2_metadata), doc2_id))
    cursor.execute(
        'INSERT INTO versions (document_id, version, change_description, file_path) VALUES (?, ?, ?, ?)',
        (doc2_id, 2, 'Published version', 'uploads/doc-b-v2.pdf')
    )
    version3_id = cursor.lastrowid
    cursor.execute('INSERT INTO html_documents (version_id, file_path) VALUES (?, ?)', (version3_id, 'uploads/doc-b-v2-html1.html'))
    cursor.execute('INSERT INTO html_documents (version_id, file_path) VALUES (?, ?)', (version3_id, 'uploads/doc-b-v2-html2.html'))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    seed_data()