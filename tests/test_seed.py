import pytest
import sqlite3
import json
from unittest.mock import patch

# Adjust the import path as necessary
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from seed import seed_data
from database import create_tables, get_db_connection

@pytest.fixture
def in_memory_db():
    # Use an in-memory SQLite database for testing
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;') # Enable foreign key enforcement
    create_tables(conn) # Create tables in the in-memory db
    yield conn

def test_seed_data(in_memory_db):
    # Call the seed_data function
    seed_data(in_memory_db)

    # Verify documents table
    cursor = in_memory_db.cursor()
    cursor.execute("SELECT * FROM documents")
    documents = cursor.fetchall()
    assert len(documents) == 2

    doc_a = next(d for d in documents if d['doc_id'] == 'doc-a')
    assert doc_a['latest_version'] == 1
    assert json.loads(doc_a['metadata'])['name'] == 'Document A'

    doc_b = next(d for d in documents if d['doc_id'] == 'doc-b')
    assert doc_b['latest_version'] == 2
    assert json.loads(doc_b['metadata'])['status'] == 'published'

    # Verify versions table
    cursor.execute("SELECT * FROM versions ORDER BY document_id, version")
    versions = cursor.fetchall()
    assert len(versions) == 3 # doc-a v1, doc-b v1, doc-b v2

    # Verify HTML documents table
    cursor.execute("SELECT * FROM html_documents")
    html_docs = cursor.fetchall()
    assert len(html_docs) == 5 # doc-a v1 (2 htmls), doc-b v1 (1 html), doc-b v2 (2 htmls)

    # Verify that clearing existing data works (run seed_data again)
    seed_data(in_memory_db) # Pass the connection here as well
    cursor.execute("SELECT * FROM documents")
    documents_after_res_seed = cursor.fetchall()
    assert len(documents_after_res_seed) == 2

    cursor.execute("SELECT * FROM versions")
    versions_after_res_seed = cursor.fetchall()
    assert len(versions_after_res_seed) == 3

    cursor.execute("SELECT * FROM html_documents")
    html_docs_after_res_seed = cursor.fetchall()
    assert len(html_docs_after_res_seed) == 5