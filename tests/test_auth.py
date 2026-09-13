def test_user_registration(client):
    res = client.post('/register', json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secretpassword"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["user"]["username"] == "alice"
    assert "api_key" in data["user"]

def test_user_login(client):
    # Register first
    client.post('/register', json={
        "username": "bob",
        "email": "bob@example.com",
        "password": "password123"
    })

    # Login
    res = client.post('/login', json={
        "username": "bob",
        "password": "password123"
    })
    assert res.status_code == 200
    assert "Login successful" in res.get_json()["message"]
