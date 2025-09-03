import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import io
import tempfile
import json
import pytest
from app import app, allowed_file
from database import create_tables

@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    client = app.test_client()

    with app.app_context():
        create_tables()

    yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

def test_allowed_file():
    assert allowed_file('test.pdf')
    assert allowed_file('test.html')
    assert not allowed_file('test.txt')
    assert not allowed_file('test')

def test_empty_db(client):
    rv = client.get('/documents')
    assert rv.status_code == 200
    assert json.loads(rv.data) == []

def test_upload_file(client):
    data = {
        'doc_id': 'doc1',
        'metadata': json.dumps({'name': 'test_pdf', 'author': 'test_author'}),
        'change_description': 'initial version',
        'file': (io.BytesIO(b"abcdef"), 'test.pdf'),
    }
    rv = client.post('/upload', content_type='multipart/form-data', data=data)
    assert rv.status_code == 200
    assert json.loads(rv.data) == {'success': True}

    rv = client.get('/documents')
    assert rv.status_code == 200
    documents = json.loads(rv.data)
    assert len(documents) == 1
    assert documents[0]['doc_id'] == 'doc1'
    assert documents[0]['metadata']['name'] == 'test_pdf'
    assert len(documents[0]['versions']) == 1
    assert documents[0]['versions'][0]['version'] == 1

def test_update_document(client):
    # First, upload a document
    data = {
        'doc_id': 'doc1',
        'metadata': json.dumps({'name': 'test_pdf', 'author': 'test_author'}),
        'change_description': 'initial version',
        'file': (io.BytesIO(b"abcdef"), 'test.pdf'),
    }
    client.post('/upload', content_type='multipart/form-data', data=data)

    # Then, upload another version of the same document with updated metadata
    data = {
        'doc_id': 'doc1',
        'metadata': json.dumps({'author': 'new_author', 'year': 2024}),
        'change_description': 'second version',
        'file': (io.BytesIO(b"ghijkl"), 'test.pdf'),
    }
    rv = client.post('/upload', content_type='multipart/form-data', data=data)
    assert rv.status_code == 200

    rv = client.get('/documents')
    assert rv.status_code == 200
    documents = json.loads(rv.data)
    assert len(documents) == 1
    assert documents[0]['doc_id'] == 'doc1'
    assert documents[0]['metadata']['name'] == 'test_pdf' # name should be preserved
    assert documents[0]['metadata']['author'] == 'new_author' # author should be updated
    assert documents[0]['metadata']['year'] == 2024 # year should be added
    assert len(documents[0]['versions']) == 2
    assert documents[0]['latest_version'] == 2

def test_search(client):
    # Upload a document
    data = {
        'doc_id': 'doc1',
        'metadata': json.dumps({'name': 'document one', 'description': 'first doc'}),
        'change_description': 'initial version',
        'file': (io.BytesIO(b"abcdef"), 'test.pdf'),
    }
    client.post('/upload', content_type='multipart/form-data', data=data)

    # Upload another document
    data = {
        'doc_id': 'doc2',
        'metadata': json.dumps({'name': 'document two', 'description': 'second doc'}),
        'change_description': 'initial version',
        'file': (io.BytesIO(b"ghijkl"), 'test.pdf'),
    }
    client.post('/upload', content_type='multipart/form-data', data=data)

    # Search for 'first'
    rv = client.get('/search?q=first')
    assert rv.status_code == 200
    documents = json.loads(rv.data)
    assert len(documents) == 1
    assert documents[0]['doc_id'] == 'doc1'

    # Search for 'second'
    rv = client.get('/search?q=second')
    assert rv.status_code == 200
    documents = json.loads(rv.data)
    assert len(documents) == 1
    assert documents[0]['doc_id'] == 'doc2'

    # Search for 'document'
    rv = client.get('/search?q=document')
    assert rv.status_code == 200
    documents = json.loads(rv.data)
    assert len(documents) == 2

def test_upload_no_file_part(client):
    rv = client.post('/upload', content_type='multipart/form-data', data={})
    assert rv.status_code == 400
    assert json.loads(rv.data) == {'error': 'No file part'}

def test_upload_empty_filename(client):
    data = {
        'file': (io.BytesIO(b''), ''),
    }
    rv = client.post('/upload', content_type='multipart/form-data', data=data)
    assert rv.status_code == 400
    assert json.loads(rv.data) == {'error': 'No selected file'}

def test_upload_invalid_file_type(client):
    data = {
        'file': (io.BytesIO(b'some text'), 'test.txt'),
    }
    rv = client.post('/upload', content_type='multipart/form-data', data=data)
    assert rv.status_code == 400
    assert json.loads(rv.data) == {'error': 'File type not allowed'}

def test_upload_invalid_metadata_json(client):
    data = {
        'doc_id': 'doc1',
        'metadata': 'invalid json',
        'change_description': 'initial version',
        'file': (io.BytesIO(b"abcdef"), 'test.pdf'),
    }
    rv = client.post('/upload', content_type='multipart/form-data', data=data)
    assert rv.status_code == 400
    assert json.loads(rv.data) == {'error': 'Invalid JSON format for metadata'}

def test_delete_version_success(client):
    # Upload a document with two versions
    data = {
        'doc_id': 'doc_del_test',
        'metadata': json.dumps({'name': 'delete test', 'version': 1}),
        'change_description': 'initial version',
        'file': (io.BytesIO(b"v1"), 'test_v1.pdf'),
    }
    client.post('/upload', content_type='multipart/form-data', data=data)

    data = {
        'doc_id': 'doc_del_test',
        'metadata': json.dumps({'name': 'delete test', 'version': 2}),
        'change_description': 'second version',
        'file': (io.BytesIO(b"v2"), 'test_v2.pdf'),
    }
    client.post('/upload', content_type='multipart/form-data', data=data)

    # Delete the first version
    rv = client.delete('/documents/doc_del_test/versions/1')
    assert rv.status_code == 200
    assert json.loads(rv.data)['success'] is True

    # Verify only one version remains
    rv = client.get('/documents')
    documents = json.loads(rv.data)
    doc = next((d for d in documents if d['doc_id'] == 'doc_del_test'), None)
    assert doc is not None
    assert len(doc['versions']) == 1
    assert doc['versions'][0]['version'] == 2
    assert doc['latest_version'] == 2

def test_delete_version_only_version(client):
    # Upload a document with one version
    data = {
        'doc_id': 'doc_only_del_test',
        'metadata': json.dumps({'name': 'only delete test'}),
        'change_description': 'initial version',
        'file': (io.BytesIO(b"only_v1"), 'only_test_v1.pdf'),
    }
    client.post('/upload', content_type='multipart/form-data', data=data)

    # Delete the only version
    rv = client.delete('/documents/doc_only_del_test/versions/1')
    assert rv.status_code == 200
    assert json.loads(rv.data)['success'] is True

    # Verify document is completely gone
    rv = client.get('/documents')
    documents = json.loads(rv.data)
    doc = next((d for d in documents if d['doc_id'] == 'doc_only_del_test'), None)
    assert doc is None

def test_delete_version_non_existent_version(client):
    # Upload a document
    data = {
        'doc_id': 'doc_non_exist_ver',
        'metadata': json.dumps({'name': 'non exist version'}),
        'change_description': 'initial version',
        'file': (io.BytesIO(b"v1"), 'test_v1.pdf'),
    }
    client.post('/upload', content_type='multipart/form-data', data=data)

    # Attempt to delete a non-existent version
    rv = client.delete('/documents/doc_non_exist_ver/versions/99')
    assert rv.status_code == 400
    assert json.loads(rv.data)['success'] is False
    assert "Version not found." in json.loads(rv.data)['error']

def test_delete_version_non_existent_doc(client):
    # Attempt to delete from a non-existent document
    rv = client.delete('/documents/non_existent_doc/versions/1')
    assert rv.status_code == 400
    assert json.loads(rv.data)['success'] is False
    assert "Document not found." in json.loads(rv.data)['error']

def test_upload_file_with_html(client):
    data = {
        'doc_id': 'doc_with_html',
        'metadata': json.dumps({'name': 'test_html_pdf'}),
        'change_description': 'initial version with html',
        'file': (io.BytesIO(b"pdf_content"), 'test.pdf'),
        'html_files': [
            (io.BytesIO(b"<html>html1</html>"), 'test1.html'),
            (io.BytesIO(b"<html>html2</html>"), 'test2.html'),
        ]
    }
    rv = client.post('/upload', content_type='multipart/form-data', data=data)
    assert rv.status_code == 200
    assert json.loads(rv.data) == {'success': True}

    rv = client.get('/documents')
    documents = json.loads(rv.data)
    doc = next((d for d in documents if d['doc_id'] == 'doc_with_html'), None)
    assert doc is not None
    assert len(doc['versions']) == 1
    assert len(doc['versions'][0]['html_paths']) == 2

def test_uploaded_file(client):
    # Upload a file first
    data = {
        'doc_id': 'doc_for_download',
        'metadata': json.dumps({'name': 'download test'}),
        'change_description': 'initial version',
        'file': (io.BytesIO(b"download_content"), 'download.pdf'),
    }
    client.post('/upload', content_type='multipart/form-data', data=data)

    # Get the document to find the actual filename generated by uuid
    rv = client.get('/documents')
    documents = json.loads(rv.data)
    doc = next((d for d in documents if d['doc_id'] == 'doc_for_download'), None)
    assert doc is not None
    file_path = doc['versions'][0]['file_path']
    filename = os.path.basename(file_path)

    # Access the uploaded file endpoint
    rv = client.get(f'/uploads/{filename}')
    assert rv.status_code == 200
    assert rv.data == b"download_content"
