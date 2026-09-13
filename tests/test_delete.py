def test_delete_missing_api_key(client):
    short_res = client.post('/shorten', json={"url": "https://example.com"})
    code = short_res.get_json()["short_code"]

    res = client.delete(f'/{code}')
    assert res.status_code == 401
    assert "Missing API key" in res.get_json()["message"]

def test_delete_invalid_api_key(client):
    short_res = client.post('/shorten', json={"url": "https://example.com"})
    code = short_res.get_json()["short_code"]

    res = client.delete(f'/{code}', headers={"X-API-Key": "invalid_key_999"})
    assert res.status_code == 401
    assert "Invalid API key" in res.get_json()["message"]

def test_delete_success_with_api_key(client, test_user):
    # Shorten URL
    short_res = client.post('/shorten', json={"url": "https://example.com/delete-me"})
    code = short_res.get_json()["short_code"]

    # Delete using test_user's API key header
    res = client.delete(f'/{code}', headers={"X-API-Key": test_user["api_key"]})
    assert res.status_code == 200
    assert "deleted successfully" in res.get_json()["message"]

    # Verify link now returns 404
    get_res = client.get(f'/{code}')
    assert get_res.status_code == 404

def test_delete_bearer_token(client, test_user):
    short_res = client.post('/shorten', json={"url": "https://example.com/bearer-test"})
    code = short_res.get_json()["short_code"]

    res = client.delete(f'/{code}', headers={"Authorization": f"Bearer {test_user['api_key']}"})
    assert res.status_code == 200
