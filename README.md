# PDF Browser

This is a simple Python web application for uploading, viewing, and searching PDF documents and their associated metadata.

## Features

- Upload PDF files with metadata (name, description, change description).
- Upload associated HTML files.
- View a list of all uploaded documents.
- Each document has a version history, which can be expanded to view older versions.
- Search for documents by name, description, or change description.

## Project Structure

```
.
├── app.py
├── database.py
├── requirements.txt
├── static
│   ├── script.js
│   └── style.css
├── templates
│   └── index.html
├── tests
│   └── test_app.py
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
