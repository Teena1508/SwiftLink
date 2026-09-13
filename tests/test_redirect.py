import time

def test_redirect_success(client):
    # Shorten a URL
    short_res = client.post('/shorten', json={"url": "https://python.org"})
    code = short_res.get_json()["short_code"]

    # Request short link redirect
    res = client.get(f'/{code}')
    assert res.status_code == 302
    assert res.headers["Location"] == "https://python.org"

    # Verify stats updated
    stats_res = client.get(f'/stats/{code}')
    assert stats_res.status_code == 200
    assert stats_res.get_json()["click_count"] == 1

def test_redirect_404_not_found(client):
    res = client.get('/nonexistentcode')
    assert res.status_code == 404

def test_redirect_410_expired_link(client):
    # Shorten with 1 second TTL
    short_res = client.post('/shorten', json={
        "url": "https://example.com/expired",
        "ttl_seconds": 1
    })
    code = short_res.get_json()["short_code"]

    # Wait for TTL to pass
    time.sleep(1.2)

    res = client.get(f'/{code}', headers={"Accept": "application/json"})
    assert res.status_code == 410
    data = res.get_json()
    assert "expired" in data["message"].lower()
