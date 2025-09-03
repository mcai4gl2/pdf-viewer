import sqlite3
from flask import current_app, g

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
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS html_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            FOREIGN KEY (version_id) REFERENCES versions (id)
        )
    ''')

    conn.commit()


def init_app(app):
    app.teardown_appcontext(close_db)


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
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS html_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            FOREIGN KEY (version_id) REFERENCES versions (id)
        )
    ''')

    conn.commit()
    conn.close()
