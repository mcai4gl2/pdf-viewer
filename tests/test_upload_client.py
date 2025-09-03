import pytest
import requests
import json
import os
from unittest.mock import patch, mock_open, MagicMock

# Assuming upload_client.py is in the parent directory
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import upload_client

@pytest.fixture
def mock_response():
    # A reusable mock response object
    m = requests.Response()
    m.status_code = 200
    m._content = json.dumps({"success": True, "message": "Upload successful!"}).encode('utf-8')
    return m

@patch('requests.post')
@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open)
def test_upload_document_success(mock_file_open, mock_os_path_exists, mock_requests_post, mock_response, capsys):
    mock_requests_post.return_value = mock_response
    mock_file_open.side_effect = [mock_open(read_data=b"pdf_content").return_value, mock_open(read_data='{"doc_id": "test_doc", "name": "Test Doc"}').return_value]

    result = upload_client.upload_document("dummy.pdf", "metadata.json")

    assert result is True
    mock_requests_post.assert_called_once()
    args, kwargs = mock_requests_post.call_args
    assert kwargs['files']['file'][0] == "dummy.pdf"
    assert kwargs['data']['doc_id'] == "test_doc"
    assert "Upload successful!" in capsys.readouterr().out

@patch('requests.post')
@patch('os.path.exists', side_effect=[True, True]) # PDF exists, metadata exists
@patch('builtins.open', new_callable=mock_open)
def test_upload_document_missing_doc_id(mock_file_open, mock_os_path_exists, mock_requests_post, capsys):
    mock_file_open.side_effect = [mock_open(read_data=b"pdf_content").return_value, mock_open(read_data='{"name": "Test Doc"}').return_value]

    result = upload_client.upload_document("dummy.pdf", "metadata.json")

    assert result is False
    mock_requests_post.assert_not_called()
    assert "Error: metadata.json must contain a 'doc_id' field." in capsys.readouterr().out

@patch('requests.post')
@patch('os.path.exists', side_effect=[False, True]) # PDF not found, metadata exists
@patch('builtins.open', new_callable=mock_open)
def test_upload_document_pdf_not_found(mock_file_open, mock_os_path_exists, mock_requests_post, capsys):
    # Mock open for metadata.json only, as PDF won't be opened
    mock_file_open.return_value.read.return_value = '{"doc_id": "test_doc"}' # For metadata.json

    result = upload_client.upload_document("non_existent.pdf", "metadata.json")

    assert result is False
    mock_requests_post.assert_not_called()
    assert "Error: PDF file not found at non_existent.pdf" in capsys.readouterr().out

@patch('requests.post')
@patch('os.path.exists', side_effect=[True, False]) # PDF exists, metadata not found
@patch('builtins.open', new_callable=mock_open)
def test_upload_document_metadata_not_found(mock_file_open, mock_os_path_exists, mock_requests_post, capsys):
    # Mock open for PDF only, as metadata won't be opened
    mock_file_open.return_value.read.return_value = b"pdf_content" # For dummy.pdf

    result = upload_client.upload_document("dummy.pdf", "non_existent_metadata.json")

    assert result is False
    mock_requests_post.assert_not_called()
    assert "Error: Metadata JSON file not found at non_existent_metadata.json" in capsys.readouterr().out

@patch('requests.post')
@patch('os.path.exists', side_effect=[True, True, False]) # PDF exists, metadata exists, HTML not found
@patch('builtins.open', new_callable=mock_open)
def test_upload_document_html_not_found(mock_file_open, mock_os_path_exists, mock_requests_post, capsys):
    mock_file_open.side_effect = [
        mock_open(read_data=b"pdf_content").return_value,
        mock_open(read_data='{"doc_id": "test_doc"}').return_value
    ]

    result = upload_client.upload_document("dummy.pdf", "metadata.json", html_file_paths=["non_existent.html"])

    assert result is False
    mock_requests_post.assert_not_called()
    assert "Error: HTML file not found at non_existent.html" in capsys.readouterr().out

@patch('requests.post')
@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open)
def test_upload_document_http_error(mock_file_open, mock_os_path_exists, mock_requests_post, mock_response, capsys):
    mock_response.status_code = 400
    mock_response._content = json.dumps({"success": False, "error": "Bad Request"}).encode('utf-8')
    mock_requests_post.return_value = mock_response
    mock_file_open.side_effect = [mock_open(read_data=b"pdf_content").return_value, mock_open(read_data='{"doc_id": "test_doc"}').return_value]

    result = upload_client.upload_document("dummy.pdf", "metadata.json")

    assert result is False
    mock_requests_post.assert_called_once()
    output = capsys.readouterr().out
    assert "Request failed: 400 Client Error: None for url: None" in output

@patch('requests.post', side_effect=requests.exceptions.RequestException("Network error"))
@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open)
def test_upload_document_request_exception(mock_file_open, mock_os_path_exists, mock_requests_post, capsys):
    mock_file_open.side_effect = [mock_open(read_data=b"pdf_content").return_value, mock_open(read_data='{"doc_id": "test_doc"}').return_value]

    result = upload_client.upload_document("dummy.pdf", "metadata.json")

    assert result is False
    mock_requests_post.assert_called_once()
    assert "Request failed: Network error" in capsys.readouterr().out

@patch('requests.post')
@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open)
def test_upload_document_with_html(mock_file_open, mock_os_path_exists, mock_requests_post, mock_response, capsys):
    mock_requests_post.return_value = mock_response
    # Mock open for PDF, metadata, html1, html2
    mock_file_open.side_effect = [
        mock_open(read_data=b"pdf_content").return_value,
        mock_open(read_data='{"doc_id": "test_doc"}').return_value,
        mock_open(read_data=b"html1_content").return_value,
        mock_open(read_data=b"html2_content").return_value
    ]

    result = upload_client.upload_document("dummy.pdf", "metadata.json", html_file_paths=["page1.html", "page2.html"])

    assert result is True
    mock_requests_post.assert_called_once()
    args, kwargs = mock_requests_post.call_args

    # Assert that 'html_files' is a list of tuples
    assert isinstance(kwargs['files']['html_files'], list)
    assert len(kwargs['files']['html_files']) == 2

    # Assert content of each HTML file tuple
    assert kwargs['files']['html_files'][0][0] == "page1.html"
    assert kwargs['files']['html_files'][0][1].read() == b"html1_content"
    assert kwargs['files']['html_files'][1][0] == "page2.html"
    assert kwargs['files']['html_files'][1][1].read() == b"html2_content"

    assert "Upload successful!" in capsys.readouterr().out

@patch('requests.post')
@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open)
def test_upload_document_json_decode_error(mock_file_open, mock_os_path_exists, mock_requests_post, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
    mock_response.text = "mocked response text" # Add this line
    mock_requests_post.return_value = mock_response
    mock_file_open.side_effect = [mock_open(read_data=b"pdf_content").return_value, mock_open(read_data='{"doc_id": "test_doc"}').return_value]

    result = upload_client.upload_document("dummy.pdf", "metadata.json")

    assert result is False
    mock_requests_post.assert_called_once()
    assert "Failed to decode JSON response: Invalid JSON: line 1 column 1 (char 0) - Response text: mocked response text" in capsys.readouterr().out

@patch('requests.post')
@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open)
def test_upload_document_generic_exception(mock_file_open, mock_os_path_exists, mock_requests_post, capsys):
    mock_response = MagicMock()
    mock_response.json.side_effect = Exception("Something unexpected happened")
    mock_requests_post.return_value = mock_response
    mock_file_open.side_effect = [mock_open(read_data=b"pdf_content").return_value, mock_open(read_data='{"doc_id": "test_doc"}').return_value]

    result = upload_client.upload_document("dummy.pdf", "metadata.json")

    assert result is False
    mock_requests_post.assert_called_once()
    assert "An unexpected error occurred: Something unexpected happened" in capsys.readouterr().out

@patch('argparse.ArgumentParser')
@patch('upload_client.upload_document')
def test_main_function(mock_upload_document, mock_argparse):
    # Mock the parser and its parse_args method
    mock_args = MagicMock()
    mock_args.pdf_path = "test.pdf"
    mock_args.metadata_json_path = "test_metadata.json"
    mock_args.html_files = ["test.html"]
    mock_args.base_url = "http://test.com"
    mock_argparse.return_value.parse_args.return_value = mock_args

    # Simulate running the script
    with patch('sys.argv', ['upload_client.py', 'test.pdf', 'test_metadata.json', '--html_files', 'test.html', '--base_url', 'http://test.com']):
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            upload_client.main() # Call the main function directly

        # Assert that upload_document was called with the correct arguments
        mock_upload_document.assert_called_once_with(
            "test.pdf",
            "test_metadata.json",
            ["test.html"],
            "http://test.com"
        )
        # Assert that the script exited with code 0 (success)
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 0

@patch('argparse.ArgumentParser')
@patch('upload_client.upload_document', return_value=False) # Simulate upload failure
def test_main_function_upload_failure(mock_upload_document, mock_argparse):
    # Mock the parser and its parse_args method
    mock_args = MagicMock()
    mock_args.pdf_path = "test.pdf"
    mock_args.metadata_json_path = "test_metadata.json"
    mock_args.html_files = None
    mock_args.base_url = "http://test.com"
    mock_argparse.return_value.parse_args.return_value = mock_args

    # Simulate running the script
    with patch('sys.argv', ['upload_client.py', 'test.pdf', 'test_metadata.json']):
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            upload_client.main() # Call the main function directly

        # Assert that upload_document was called with the correct arguments
        mock_upload_document.assert_called_once_with(
            "test.pdf",
            "test_metadata.json",
            None,
            "http://test.com"
        )
        # Assert that the script exited with code 1 (failure)
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1
