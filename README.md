# PDF Browser

[![codecov](https://codecov.io/gh/mcai4gl2/pdf-viewer/branch/main/graph/badge.svg)](https://codecov.io/gh/mcai4gl2/pdf-viewer)

This is a simple Python web application for uploading, viewing, and searching PDF documents and their associated metadata.

## Features

- Upload PDF files with metadata (name, description, change description).
- Upload associated HTML files.
- View a list of all uploaded documents.
- Each document has a version history, which can be expanded to view older versions.
- Search for documents by name, description, or change description.
- **Improved Aesthetics**: Integrated `mini.css` for a cleaner and more modern look.
- **Delete Version Functionality**: Users can now delete specific versions of documents. This includes proper cleanup of associated files and database entries. Deleting the last version of a document will remove the document entirely.
- **User Voting**: Users can now vote on the quality of document versions directly from the main document listing page using 'Good' and 'Bad' buttons. Votes are stored in the database along with voter information (e.g., IP address) and a timestamp. A dedicated page (`/vote_results_page`) is available to view the aggregated voting results (counts of good/bad votes per version).

## Project Structure

```
.
├── API.md
├── app.py
├── database.py
├── requirements.txt
├── seed.py
├── SoftwareRequirement.md
├── upload_client.py
├── static
│   ├── script.js
│   ├── style.css
│   ├── upload.js
│   └── vote_results.js
├── templates
│   ├── index.html
│   ├── upload.html
│   └── vote_results.html
├── tests
│   ├── test_app.py
│   ├── test_database.py
│   └── test_upload_client.py
├── uploads
├── venv
└── docs
    └── upload_client_guide.md
```

## Getting Started

### Prerequisites

- Python 3
- `venv` module for Python

### Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd pdf-browser
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the database:**

    ```bash
    python database.py
    ```

5.  **Seed the database with test data (optional):**

    ```bash
    python seed.py
    ```

### Running the Application

To start the Flask development server, run:

```bash
python app.py
```

The application will be available at `http://172.0.0.1:5000`.

### Running Tests

To run the tests, use `pytest`:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=.
```

## Test Coverage

```
Name                          Stmts   Miss  Cover
-------------------------------------------------
app.py                          163     22    87%
database.py                     127     30    76%
seed.py                          38      5    87%
tests/test_app.py               159      0   100%
tests/test_database.py          256      1    99%
tests/test_seed.py               44      0   100%
tests/test_upload_client.py     158      0   100%
upload_client.py                 76      4    95%
-------------------------------------------------
TOTAL                          1021     62    94%
```

## API Documentation

For details on the REST API endpoints, refer to [API.md](API.md).

## Client Script

The `upload_client.py` script provides a command-line interface to programmatically upload documents to the PDF Browser application. For detailed usage instructions and examples, refer to the [Upload Client Guide](docs/upload_client_guide.md).
