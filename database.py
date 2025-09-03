import sqlite3
from flask import current_app, g
import os
import json

DATABASE_NAME = 'pdf_browser.db'

def get_db_connection():
    if 'db' not in g:
        if current_app.config.get('DATABASE'):
            g.db = sqlite3.connect(
                current_app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
        else:
            g.db = sqlite3.connect(
                DATABASE_NAME,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON;') # Enable foreign key enforcement

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT NOT NULL UNIQUE,
            metadata TEXT,
            latest_version INTEGER DEFAULT 1
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            change_description TEXT,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS html_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            FOREIGN KEY (version_id) REFERENCES versions (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            version_id INTEGER NOT NULL,
            vote_type TEXT NOT NULL,
            voter_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
            FOREIGN KEY (version_id) REFERENCES versions (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()

def init_app(app):
    app.teardown_appcontext(close_db)

def delete_document_version(doc_id, version_number):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get document_id from doc_id
        cursor.execute('SELECT id FROM documents WHERE doc_id = ?', (doc_id,))
        document = cursor.fetchone()
        if not document:
            return False, "Document not found."
        document_id = document['id']

        # Get version details
        cursor.execute('SELECT id, file_path FROM versions WHERE document_id = ? AND version = ?', (document_id, version_number))
        version_to_delete = cursor.fetchone()
        if not version_to_delete:
            return False, "Version not found."

        version_id = version_to_delete['id']
        file_path_to_delete = version_to_delete['file_path']

        # Get associated HTML files
        cursor.execute('SELECT file_path FROM html_documents WHERE version_id = ?', (version_id,))
        html_files_to_delete = cursor.fetchall()

        # Delete HTML documents from filesystem
        for html_file in html_files_to_delete:
            if os.path.exists(html_file['file_path']):
                os.remove(html_file['file_path'])

        # Delete main PDF file from filesystem
        if os.path.exists(file_path_to_delete):
            os.remove(file_path_to_delete)

        # Delete from html_documents table
        cursor.execute('DELETE FROM html_documents WHERE version_id = ?', (version_id,))

        # Delete from versions table
        cursor.execute('DELETE FROM versions WHERE id = ?', (version_id,))

        # Check if this was the latest version and update documents table if necessary
        cursor.execute('SELECT MAX(version) as max_version FROM versions WHERE document_id = ?', (document_id,))
        max_version_row = cursor.fetchone()
        max_version = max_version_row['max_version'] if max_version_row and max_version_row['max_version'] is not None else 0

        cursor.execute('UPDATE documents SET latest_version = ? WHERE id = ?', (max_version, document_id))

        # If no versions remain, delete the document entry itself
        if max_version == 0:
            cursor.execute('DELETE FROM documents WHERE id = ?', (document_id,))

        conn.commit()
        return True, "Version deleted successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)

def insert_vote(doc_id, version_number, vote_type, voter_info):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM documents WHERE doc_id = ?', (doc_id,))
        document = cursor.fetchone()
        if not document:
            return False, "Document not found."
        document_id = document['id']

        cursor.execute('SELECT id FROM versions WHERE document_id = ? AND version = ?', (document_id, version_number))
        version_data = cursor.fetchone()
        if not version_data:
            return False, "Version not found."
        version_id = version_data['id']

        cursor.execute('INSERT INTO votes (document_id, version_id, vote_type, voter_info) VALUES (?, ?, ?, ?)',
                       (document_id, version_id, vote_type, voter_info))
        conn.commit()
        return True, "Vote recorded successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)

def get_vote_counts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            d.doc_id,
            v.version,
            SUM(CASE WHEN t.vote_type = 'good' THEN 1 ELSE 0 END) AS good_votes,
            SUM(CASE WHEN t.vote_type = 'bad' THEN 1 ELSE 0 END) AS bad_votes
        FROM votes t
        JOIN documents d ON t.document_id = d.id
        JOIN versions v ON t.version_id = v.id
        GROUP BY d.doc_id, v.version
        ORDER BY d.doc_id, v.version
    ''')
    results = cursor.fetchall()
    return [dict(row) for row in results]

def get_all_individual_votes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            d.doc_id,
            v.version,
            t.vote_type,
            t.voter_info,
            t.created_at
        FROM votes t
        JOIN documents d ON t.document_id = d.id
        JOIN versions v ON t.version_id = v.id
        ORDER BY d.doc_id, v.version, t.created_at
    ''')
    results = cursor.fetchall()
    return [dict(row) for row in results]


if __name__ == '__main__':
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT NOT NULL UNIQUE,
            metadata TEXT,
            latest_version INTEGER DEFAULT 1
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            change_description TEXT,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS html_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            FOREIGN KEY (version_id) REFERENCES versions (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            version_id INTEGER NOT NULL,
            vote_type TEXT NOT NULL,
            voter_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
            FOREIGN KEY (version_id) REFERENCES versions (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()


    print("Database initialized and tables created.")

    # Example of adding a document and version
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    doc_id = "example_doc_1"
    metadata = json.dumps({"title": "Example Document", "author": "Gemini"})
    file_path = "uploads/example_doc_1_v1.pdf"
    change_description = "Initial upload"

    cursor.execute('INSERT OR IGNORE INTO documents (doc_id, metadata) VALUES (?, ?)', (doc_id, metadata))
    document_id = cursor.lastrowid

    # If document already exists, get its ID
    if not document_id:
        cursor.execute('SELECT id FROM documents WHERE doc_id = ?', (doc_id,))
        document_id = cursor.fetchone()['id']

    cursor.execute(
        'INSERT INTO versions (document_id, version, change_description, file_path) VALUES (?, ?, ?, ?)',
        (document_id, 1, change_description, file_path)
    )
    conn.commit()
    conn.close()
    print(f"Added example document: {doc_id}, version 1")