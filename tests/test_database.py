import os
import tempfile
import pytest
from flask import Flask
from app import app
from database import get_db_connection, create_tables, close_db, init_app, delete_document_version, insert_vote, get_vote_counts, get_all_individual_votes
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

        # Add a document for voting tests
        cursor.execute('INSERT INTO documents (doc_id, metadata, latest_version) VALUES (?, ?, ?)', ('doc_vote', '{}', 1))
        doc_vote_id = cursor.lastrowid
        cursor.execute('INSERT INTO versions (document_id, version, file_path) VALUES (?, ?, ?)', (doc_vote_id, 1, 'uploads/doc_vote_v1.pdf'))
        vote_v1_id = cursor.lastrowid

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

def test_insert_vote_success(populated_database):
    with app.app_context():
        success, message = insert_vote('doc_vote', 1, 'good', '127.0.0.1')
        assert success is True
        assert "Vote recorded successfully." in message

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM votes WHERE document_id = (SELECT id FROM documents WHERE doc_id = ?) AND version_id = (SELECT id FROM versions WHERE document_id = (SELECT id FROM documents WHERE doc_id = ?) AND version = ?) AND vote_type = ? AND voter_info = ?', ('doc_vote', 'doc_vote', 1, 'good', '127.0.0.1'))
        vote = cursor.fetchone()
        assert vote is not None

def test_insert_vote_non_existent_doc(populated_database):
    with app.app_context():
        success, message = insert_vote('non_existent_doc', 1, 'good', '127.0.0.1')
        assert success is False
        assert "Document not found." in message

def test_insert_vote_non_existent_version(populated_database):
    with app.app_context():
        success, message = insert_vote('doc_vote', 99, 'good', '127.0.0.1')
        assert success is False
        assert "Version not found." in message

@patch('os.remove')
@patch('os.path.exists', return_value=True)
def test_delete_document_version_cascades_votes(mock_exists, mock_remove, populated_database):
    with app.app_context():
        # Insert a vote first
        insert_vote('doc1', 1, 'good', '127.0.0.1')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM votes')
        initial_vote_count = cursor.fetchone()[0]
        assert initial_vote_count > 0

        # Delete version 1 of doc1
        success, message = delete_document_version('doc1', 1)
        assert success is True

        # Verify vote is deleted
        cursor.execute('SELECT COUNT(*) FROM votes WHERE document_id = (SELECT id FROM documents WHERE doc_id = ?) AND version_id = (SELECT id FROM versions WHERE document_id = (SELECT id FROM documents WHERE doc_id = ?) AND version = ?)', ('doc1', 'doc1', 1))
        remaining_votes = cursor.fetchone()[0]
        assert remaining_votes == 0

@patch('os.remove')
@patch('os.path.exists', return_value=True)
def test_delete_document_cascades_votes(mock_exists, mock_remove, populated_database):
    with app.app_context():
        # Insert a vote for doc2 (which has only one version)
        insert_vote('doc2', 1, 'good', '127.0.0.1')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM votes')
        initial_vote_count = cursor.fetchone()[0]
        assert initial_vote_count > 0

        # Delete the only version of doc2
        success, message = delete_document_version('doc2', 1)
        assert success is True

        # Verify vote is deleted (document and version are gone, so vote should be too)
        cursor.execute('SELECT COUNT(*) FROM votes WHERE voter_info = ?', ('127.0.0.1',))
        remaining_votes = cursor.fetchone()[0]
        assert remaining_votes == 0

@patch('os.remove')
@patch('os.path.exists', return_value=False) # Files do not exist
def test_delete_document_version_files_not_exist(mock_exists, mock_remove, populated_database):
    with app.app_context():
        # Delete version 1 of doc1
        success, message = delete_document_version('doc1', 1)
        assert success is True
        assert "Version deleted successfully." in message
        mock_remove.assert_not_called() # os.remove should not be called if files don't exist

@patch('database.get_db_connection')
def test_insert_vote_exception_handling(mock_get_db_connection, populated_database):
    with app.app_context():
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value = mock_conn

        mock_cursor.execute.side_effect = Exception("Vote database error")

        success, message = insert_vote('doc_vote', 1, 'good', '127.0.0.1')
        assert success is False
        assert "Vote database error" in message
        mock_conn.rollback.assert_called_once()

def test_get_vote_counts(populated_database):
    with app.app_context():
        # Insert some votes first
        insert_vote('doc_vote', 1, 'good', 'voter1')
        insert_vote('doc_vote', 1, 'good', 'voter2')
        insert_vote('doc_vote', 1, 'bad', 'voter3')

        counts = get_vote_counts()
        assert isinstance(counts, list)
        assert len(counts) > 0
        
        # Find the entry for doc_vote version 1
        doc_vote_counts = next((item for item in counts if item['doc_id'] == 'doc_vote' and item['version'] == 1), None)
        assert doc_vote_counts is not None
        assert doc_vote_counts['good_votes'] >= 2
        assert doc_vote_counts['bad_votes'] >= 1

def test_get_all_individual_votes(populated_database):
    with app.app_context():
        # Insert some votes first
        insert_vote('doc_vote', 1, 'good', 'voter_A')
        insert_vote('doc_vote', 1, 'bad', 'voter_B')

        votes = get_all_individual_votes()
        assert isinstance(votes, list)
        assert len(votes) > 0

        # Check for specific votes
        voter_a_vote = next((item for item in votes if item['doc_id'] == 'doc_vote' and item['voter_info'] == 'voter_A'), None)
        assert voter_a_vote is not None
        assert voter_a_vote['vote_type'] == 'good'

        voter_b_vote = next((item for item in votes if item['doc_id'] == 'doc_vote' and item['voter_info'] == 'voter_B'), None)
        assert voter_b_vote is not None
        assert voter_b_vote['vote_type'] == 'bad'

@patch('os.remove')
@patch('os.path.exists', return_value=True)
def test_delete_document_version_deletes_document_if_no_versions_remain(mock_exists, mock_remove, populated_database):
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ensure doc2 has only one version (it does in populated_database)
        # Delete the only version of doc2
        success, message = delete_document_version('doc2', 1)
        assert success is True
        assert "Version deleted successfully." in message

        # Verify doc2 is deleted from the documents table
        cursor.execute('SELECT * FROM documents WHERE doc_id = ?', ('doc2',))
        assert cursor.fetchone() is None

        # Verify os.remove was called for the PDF and HTML file
        mock_remove.assert_any_call('uploads/doc2_v1.pdf')
        mock_remove.assert_any_call('uploads/doc2_v1.html')
