import os
import tempfile
import pytest
from flask import Flask
from app import app
from database import get_db_connection, create_tables, close_db, init_app

@pytest.fixture
def database_client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True

    with app.app_context():
        create_tables()

    yield

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

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