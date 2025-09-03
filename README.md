# PDF Browser

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
│   └── test_database.py
├── uploads
└── venv
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

The application will be available at `http://127.0.0.1:5000`.

### Running Tests

To run the tests, use `pytest`:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=.
```

## API Documentation

For details on the REST API endpoints, refer to [API.md](API.md).