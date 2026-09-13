def test_custom_rate_limiter_exceeded(client):
    # RATE_LIMIT_PER_MINUTE is set to 5 in TestingConfig
    url_payload = {"url": "https://example.com/rate-limit"}

    # First 5 requests should succeed
    for _ in range(5):
        res = client.post('/shorten', json=url_payload)
        assert res.status_code == 201

    # 6th request should hit rate limit (429)
    res_exceeded = client.post('/shorten', json=url_payload)
    assert res_exceeded.status_code == 429
    data = res_exceeded.get_json()
    assert data["error"] == "Rate limit exceeded"
    assert "Retry-After" in res_exceeded.headers
    assert int(res_exceeded.headers["Retry-After"]) >= 1
