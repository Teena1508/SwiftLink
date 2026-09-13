from app.utils.generator import generate_unique_short_code, base62_encode
from app.utils.rate_limiter import rate_limiter

def test_shorten_valid_url(client):
    rate_limiter.reset()
    response = client.post('/shorten', json={
        "url": "https://example.com/test-path"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "short_code" in data
    assert "short_url" in data
    assert data["original_url"] == "https://example.com/test-path"
    assert len(data["short_code"]) == 6

def test_shorten_invalid_url_schemes(client):
    rate_limiter.reset()
    invalid_urls = [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "data:text/html,test",
        "ftp://example.com/file",
        "httpx://unknown-scheme.com",
        "not-a-url"
    ]
    for url in invalid_urls:
        rate_limiter.reset()
        res = client.post('/shorten', json={"url": url})
        assert res.status_code == 400
        data = res.get_json()
        assert "message" in data

def test_custom_alias_valid(client):
    rate_limiter.reset()
    response = client.post('/shorten', json={
        "url": "https://example.com",
        "custom_alias": "my-custom-code"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["short_code"] == "my-custom-code"
    assert data["is_custom_alias"] is True

def test_custom_alias_collision(client):
    rate_limiter.reset()
    # Create first alias
    client.post('/shorten', json={
        "url": "https://example.com/1",
        "custom_alias": "unique-alias"
    })
    # Attempt second alias with same code
    res = client.post('/shorten', json={
        "url": "https://example.com/2",
        "custom_alias": "unique-alias"
    })
    assert res.status_code == 409
    data = res.get_json()
    assert "already in use" in data["message"]

def test_custom_alias_reserved_slug(client):
    rate_limiter.reset()
    res = client.post('/shorten', json={
        "url": "https://example.com",
        "custom_alias": "shorten"
    })
    assert res.status_code == 400
    assert "reserved system keyword" in res.get_json()["message"]

def test_shorten_with_ttl(client):
    rate_limiter.reset()
    res = client.post('/shorten', json={
        "url": "https://example.com/ttl",
        "ttl_seconds": 3600
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["expires_at"] is not None

def test_base62_encoding_and_generator():
    assert base62_encode(0) == "0"
    assert base62_encode(61) == "Z"
    assert base62_encode(62) == "10"

    existing_set = set()
    def mock_checker(code):
        return code in existing_set

    code1 = generate_unique_short_code("https://example.com", mock_checker, length=6)
    existing_set.add(code1)
    code2 = generate_unique_short_code("https://example.com", mock_checker, length=6)
    assert code1 != code2
