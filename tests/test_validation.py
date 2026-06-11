def test_missing_url_returns_400(client):
    response = client.post("/shorten", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "URL is required"


def test_empty_url_returns_400(client):
    response = client.post("/shorten", json={"url": ""})

    assert response.status_code == 400
    assert response.json()["detail"] == "URL is required"


def test_alias_too_long_returns_400(client):
    response = client.post(
        "/shorten",
        json={"url": "https://example.com/a", "alias": "a" * 33},
    )

    assert response.status_code == 400
