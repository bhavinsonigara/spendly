def test_login_get_renders_form(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_login_blank_both_fields(client):
    response = client.post("/login", data={"email": "", "password": ""})
    assert b"All fields are required." in response.data


def test_login_blank_email(client):
    response = client.post("/login", data={"email": "", "password": "password123"})
    assert b"All fields are required." in response.data


def test_login_blank_password(client):
    response = client.post("/login", data={"email": "test@example.com", "password": ""})
    assert b"All fields are required." in response.data


def test_login_unknown_email(client):
    response = client.post("/login", data={"email": "nobody@example.com", "password": "password123"})
    assert b"Invalid email or password." in response.data


def test_login_wrong_password(client):
    response = client.post("/login", data={"email": "test@example.com", "password": "wrongpassword"})
    assert b"Invalid email or password." in response.data


def test_login_success_redirects(client):
    response = client.post("/login", data={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_login_success_sets_session(client):
    client.post("/login", data={"email": "test@example.com", "password": "password123"})
    with client.session_transaction() as sess:
        assert sess["user_name"] == "Test User"
        assert "user_id" in sess


def test_logout_redirects_to_landing(client):
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_logout_clears_session(client):
    client.post("/login", data={"email": "test@example.com", "password": "password123"})
    client.get("/logout")
    with client.session_transaction() as sess:
        assert "user_id" not in sess
        assert "user_name" not in sess


def test_already_logged_in_redirects_from_login(client):
    client.post("/login", data={"email": "test@example.com", "password": "password123"})
    response = client.get("/login")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_already_logged_in_redirects_from_register_get(client):
    client.post("/login", data={"email": "test@example.com", "password": "password123"})
    response = client.get("/register")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_already_logged_in_redirects_from_register_post(client):
    client.post("/login", data={"email": "test@example.com", "password": "password123"})
    response = client.post("/register", data={"name": "X", "email": "x@x.com", "password": "password123"})
    assert response.status_code == 302
    assert response.headers["Location"] == "/"
