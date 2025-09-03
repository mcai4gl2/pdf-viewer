# Upload Client Guide

This guide explains how to use the `upload_client.py` script to programmatically upload documents (PDFs, metadata, and optional HTML files) to the PDF Browser application.

## Purpose

The `upload_client.py` script provides a command-line interface to interact with the PDF Browser's `POST /upload` API endpoint. It automates the process of preparing and sending multipart/form-data requests, making it easy to integrate document uploads into other scripts or workflows.

## Prerequisites

Before using the script, ensure you have the following:

-   **Python 3**: The script is written in Python 3.
-   **`requests` library**: This Python library is used for making HTTP requests. You can install it using pip:

    ```bash
    pip install requests
    ```

-   **PDF Browser Application**: The PDF Browser application must be running and accessible at the specified `base_url` (default: `http://127.0.0.1:5000`).

## `metadata.json` Structure

The `metadata.json` file is a crucial component of the upload process. It must be a valid JSON object and **must contain a `doc_id` field**. This `doc_id` is used to identify the document for both initial uploads and subsequent updates (new versions).

Here's an example of a `metadata.json` file:

```json
{
    "doc_id": "your_unique_document_id",
    "name": "My Awesome Document",
    "author": "John Doe",
    "change_description": "Initial upload of the document",
    "keywords": ["report", "annual", "2023"]
}
```

-   `doc_id` (string, **required**): A unique identifier for your document. If you upload a new document with an existing `doc_id`, it will create a new version of that document.
-   `name` (string, optional): The name of the document.
-   `author` (string, optional): The author of the document.
-   `change_description` (string, optional): A description of the changes made in this version. If not provided, a default message will be used.
-   Other fields: You can include any other key-value pairs in the `metadata.json` file. These will be stored as part of the document's metadata.

## Command-Line Arguments

The `upload_client.py` script accepts the following command-line arguments:

-   `<pdf_path>` (positional, **required**): Path to the PDF file you want to upload.
-   `<metadata_json_path>` (positional, **required**): Path to the JSON file containing the document's metadata.
-   `--html_files` (optional, multiple values): A space-separated list of paths to HTML files to associate with this document version.
-   `--base_url` (optional, default: `http://127.0.0.1:5000`): The base URL of the PDF Browser application.

## How to Run the Script

1.  **Ensure prerequisites are met** (Python 3, `requests` installed).
2.  **Prepare your files**: Have your PDF, `metadata.json`, and any optional HTML files ready.
3.  **Run the script** from your terminal:

### Examples

#### 1. Upload a PDF with metadata only

```bash
# Create dummy files for demonstration
echo "This is a dummy PDF content." > dummy.pdf
cat <<EOF > metadata.json
{
    "doc_id": "my_first_doc",
    "name": "My First Document",
    "author": "Client Script",
    "change_description": "Initial upload via client script"
}
EOF

python upload_client.py dummy.pdf metadata.json
```

#### 2. Upload a PDF with metadata and associated HTML files

```bash
# Create dummy HTML files
echo "<html><body>Page 1</body></html>" > page1.html
echo "<html><body>Page 2</body></html>" > page2.html

python upload_client.py dummy.pdf metadata.json --html_files page1.html page2.html
```

#### 3. Update an existing document (create a new version)

To update a document, use the same `doc_id` in your `metadata.json` file. The application will automatically create a new version.

```bash
# Create a new PDF file for the update
echo "This is the updated PDF content." > dummy_updated.pdf

# Update metadata.json (e.g., change change_description or add new fields)
cat <<EOF > metadata_updated.json
{
    "doc_id": "my_first_doc",
    "name": "My First Document",
    "author": "Client Script",
    "change_description": "Updated via client script - second version",
    "new_field": "some_value"
}
EOF

# Upload the updated document with new HTML files
echo "<html><body>Page 3</body></html>" > page3.html
python upload_client.py dummy_updated.pdf metadata_updated.json --html_files page3.html
```

Upon successful upload, the script will print a success message. In case of errors, it will provide an error message from the server or a network error description.
