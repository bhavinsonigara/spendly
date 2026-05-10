import pytest
from werkzeug.security import generate_password_hash
import database.db as db_module
from app import app as flask_app


@pytest.fixture
def app(tmp_path):
    db_module.DB_PATH = str(tmp_path / "test.db")

    flask_app.config["TESTING"] = True

    with flask_app.app_context():
        db_module.init_db()
        conn = db_module.get_db()
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Test User", "test@example.com", generate_password_hash("password123")),
        )
        conn.commit()
        conn.close()

    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()
