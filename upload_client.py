import requests
import json
import argparse
import os

def upload_document(pdf_path, metadata_json_path, html_file_paths=None, base_url="http://127.0.0.1:5000"):
    """
    Uploads a document (PDF, metadata, and optional HTML files) to the PDF Browser application.

    Args:
        pdf_path (str): Path to the PDF file.
        metadata_json_path (str): Path to the JSON file containing metadata.
        html_file_paths (list, optional): List of paths to HTML files. Defaults to None.
        base_url (str, optional): Base URL of the PDF Browser application. Defaults to "http://127.0.0.1:5000".
    """
    upload_url = f"{base_url}/upload"

    # Basic validation moved here, return False on error
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return False
    if not os.path.exists(metadata_json_path):
        print(f"Error: Metadata JSON file not found at {metadata_json_path}")
        return False
    if html_file_paths:
        for html_file in html_file_paths:
            if not os.path.exists(html_file):
                print(f"Error: HTML file not found at {html_file}")
                return False

    # Prepare files for multipart/form-data
    pdf_file_handle = None
    html_file_handles = []
    try:
        pdf_file_handle = open(pdf_path, 'rb')
        files = [
            ('file', (os.path.basename(pdf_path), pdf_file_handle, 'application/pdf'))
        ]

        # Read metadata JSON
        with open(metadata_json_path, 'r') as f:
            metadata = json.load(f)
        
        # Extract doc_id and ensure it's in the form data
        doc_id = metadata.get('doc_id')
        if not doc_id:
            print("Error: metadata.json must contain a 'doc_id' field.")
            return False

        data = {
            'doc_id': doc_id,
            'metadata': json.dumps(metadata),
            'change_description': metadata.get('change_description', 'Uploaded via client script')
        }

        # Add HTML files if provided
        if html_file_paths:
            for html_path in html_file_paths:
                html_file_handle = open(html_path, 'rb')
                files.append(('html_files', (os.path.basename(html_path), html_file_handle, 'text/html')))
                html_file_handles.append(html_file_handle)

        print(f"Uploading to: {upload_url}")
        print(f"Doc ID: {doc_id}")
        print(f"Metadata: {data['metadata']}")
        if html_file_paths:
            print(f"HTML Files: {[os.path.basename(p) for p in html_file_paths]}") # Print basenames

        response = requests.post(upload_url, files=files, data=data)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        result = response.json()
        if result.get('success'):
            print("Upload successful!")
            print(f"Response: {result}")
            return True # Indicate success
        else:
            print("Upload failed.")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False # Indicate failure
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False # Indicate failure
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON response: {e} - Response text: {response.text}")
        return False # Indicate failure
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
    finally:
        # Ensure all opened files are closed
        if pdf_file_handle:
            pdf_file_handle.close()
        for hf in html_file_handles:
            hf.close()

def main():
    parser = argparse.ArgumentParser(description="Upload a document to the PDF Browser application.")
    parser.add_argument("pdf_path", help="Path to the PDF file.")
    parser.add_argument("metadata_json_path", help="Path to the JSON file containing metadata.")
    parser.add_argument("--html_files", nargs='*', help="List of paths to HTML files (optional).")
    parser.add_argument("--base_url", default="http://127.0.0.1:5000", help="Base URL of the PDF Browser application.")

    args = parser.parse_args()

    # Call upload_document and exit based on its return value
    if upload_document(args.pdf_path, args.metadata_json_path, args.html_files, args.base_url):
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()