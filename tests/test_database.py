import os
import tempfile
import pytest
from flask import Flask
from app import app
from database import get_db_connection, create_tables, close_db, init_app, delete_document_version
import json
from unittest.mock import patch, MagicMock

@pytest.fixture
def database_client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True

    with app.app_context():
        create_tables()

    yield

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

@pytest.fixture
def populated_database(database_client):
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()

        # Add a document with multiple versions
        cursor.execute('INSERT INTO documents (doc_id, metadata, latest_version) VALUES (?, ?, ?)', ('doc1', '{}', 2))
        doc1_id = cursor.lastrowid

        cursor.execute('INSERT INTO versions (document_id, version, file_path) VALUES (?, ?, ?)', (doc1_id, 1, 'uploads/doc1_v1.pdf'))
        v1_id = cursor.lastrowid
        cursor.execute('INSERT INTO html_documents (version_id, file_path) VALUES (?, ?)', (v1_id, 'uploads/doc1_v1.html'))

        cursor.execute('INSERT INTO versions (document_id, version, file_path) VALUES (?, ?, ?)', (doc1_id, 2, 'uploads/doc1_v2.pdf'))
        v2_id = cursor.lastrowid
        cursor.execute('INSERT INTO html_documents (version_id, file_path) VALUES (?, ?)', (v2_id, 'uploads/doc1_v2.html'))

        # Add a document with a single version
        cursor.execute('INSERT INTO documents (doc_id, metadata, latest_version) VALUES (?, ?, ?)', ('doc2', '{}', 1))
        doc2_id = cursor.lastrowid

        cursor.execute('INSERT INTO versions (document_id, version, file_path) VALUES (?, ?, ?)', (doc2_id, 1, 'uploads/doc2_v1.pdf'))
        v3_id = cursor.lastrowid
        cursor.execute('INSERT INTO html_documents (version_id, file_path) VALUES (?, ?)', (v3_id, 'uploads/doc2_v1.html'))

        conn.commit()

def test_get_db_connection(database_client):
    with app.app_context():
        conn = get_db_connection()
        assert conn is not None
        assert conn == get_db_connection() # Should return the same connection

def test_get_db_connection_no_config():
    with app.app_context():
        # Temporarily remove DATABASE from config to test the else branch
        original_db_config = app.config.pop('DATABASE', None)
        conn = get_db_connection()
        assert conn is not None
        assert conn == get_db_connection() # Should return the same connection
        # Restore original config
        if original_db_config:
            app.config['DATABASE'] = original_db_config

def test_close_db(database_client):
    with app.app_context():
        conn = get_db_connection()
        close_db()
        try:
            conn.execute('SELECT 1')
            assert False, "Connection should be closed"
        except Exception as e:
            assert "closed" in str(e) or "no such database" in str(e)

def test_init_app():
    test_app = Flask(__name__)
    with test_app.app_context():
        init_app(test_app)
        assert close_db in test_app.teardown_appcontext_funcs

def test_create_tables(database_client):
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()

        # Try inserting into tables to confirm they exist
        cursor.execute('INSERT INTO documents (doc_id, metadata) VALUES (?, ?)', ('test_doc', '{}'))
        doc_id = cursor.lastrowid
        assert doc_id is not None

        cursor.execute('INSERT INTO versions (document_id, version, file_path) VALUES (?, ?, ?)', (doc_id, 1, 'path/to/file.pdf'))
        version_id = cursor.lastrowid
        assert version_id is not None

        cursor.execute('INSERT INTO html_documents (version_id, file_path) VALUES (?, ?)', (version_id, 'path/to/html.html'))
        html_id = cursor.lastrowid
        assert html_id is not None

        conn.commit()

@patch('os.remove')
@patch('os.path.exists', return_value=True)
def test_delete_document_version_specific_version(mock_exists, mock_remove, populated_database):
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete version 1 of doc1
        success, message = delete_document_version('doc1', 1)
        assert success is True
        assert "Version deleted successfully." in message

        # Verify version 1 is deleted
        cursor.execute('SELECT * FROM versions WHERE document_id = (SELECT id FROM documents WHERE doc_id = ?) AND version = ?', ('doc1', 1))
        assert cursor.fetchone() is None

        # Verify associated html files are deleted from db
        cursor.execute('SELECT * FROM html_documents WHERE file_path = ?', ('uploads/doc1_v1.html',))
        assert cursor.fetchone() is None

        # Verify os.remove was called for the PDF and HTML file
        mock_remove.assert_any_call('uploads/doc1_v1.pdf')
        mock_remove.assert_any_call('uploads/doc1_v1.html')

        # Verify doc1 still exists and latest_version is updated
        cursor.execute('SELECT latest_version FROM documents WHERE doc_id = ?', ('doc1',))
        doc1 = cursor.fetchone()
        assert doc1 is not None
        assert doc1['latest_version'] == 2 # latest_version should now be 2

        # Verify version 2 of doc1 still exists
        cursor.execute('SELECT * FROM versions WHERE document_id = (SELECT id FROM documents WHERE doc_id = ?) AND version = ?', ('doc1', 2))
        assert cursor.fetchone() is not None

@patch('os.remove')
@patch('os.path.exists', return_value=True)
def test_delete_document_version_only_version(mock_exists, mock_remove, populated_database):
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete version 1 of doc2 (which is the only version)
        success, message = delete_document_version('doc2', 1)
        assert success is True
        assert "Version deleted successfully." in message

        # Verify version 1 is deleted
        cursor.execute('SELECT * FROM versions WHERE document_id = (SELECT id FROM documents WHERE doc_id = ?) AND version = ?', ('doc2', 1))
        assert cursor.fetchone() is None

        # Verify doc2 is deleted
        cursor.execute('SELECT * FROM documents WHERE doc_id = ?', ('doc2',))
        assert cursor.fetchone() is None

        # Verify os.remove was called for the PDF and HTML file
        mock_remove.assert_any_call('uploads/doc2_v1.pdf')
        mock_remove.assert_any_call('uploads/doc2_v1.html')

@patch('os.remove')
@patch('os.path.exists', return_value=True)
def test_delete_document_version_non_existent_version(mock_exists, mock_remove, populated_database):
    with app.app_context():
        success, message = delete_document_version('doc1', 99)
        assert success is False
        assert "Version not found." in message
        mock_remove.assert_not_called()

@patch('os.remove')
@patch('os.path.exists', return_value=True)
def test_delete_document_version_non_existent_doc(mock_exists, mock_remove, populated_database):
    with app.app_context():
        success, message = delete_document_version('non_existent_doc', 1)
        assert success is False
        assert "Document not found." in message
        mock_remove.assert_not_called()

@patch('database.get_db_connection')
@patch('os.remove')
@patch('os.path.exists', return_value=True)
def test_delete_document_version_exception_handling(mock_exists, mock_remove, mock_get_db_connection, populated_database):
    with app.app_context():
        # Mock the connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value = mock_conn

        # Make cursor.execute raise an exception on its first call
        mock_cursor.execute.side_effect = Exception("Database error during test")

        success, message = delete_document_version('doc1', 1)

        assert success is False
        assert "Database error during test" in message
        mock_conn.rollback.assert_called_once()
        mock_remove.assert_not_called() # Ensure no file operations if DB fails early