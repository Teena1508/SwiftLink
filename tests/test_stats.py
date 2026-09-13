def test_get_stats_success(client):
    short_res = client.post('/shorten', json={"url": "https://flask.palletsprojects.com"})
    code = short_res.get_json()["short_code"]

    res = client.get(f'/stats/{code}')
    assert res.status_code == 200
    data = res.get_json()
    assert data["short_code"] == code
    assert data["original_url"] == "https://flask.palletsprojects.com"
    assert data["click_count"] == 0
    assert "created_at" in data

def test_get_stats_not_found(client):
    res = client.get('/stats/missingcode')
    assert res.status_code == 404
