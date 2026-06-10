def test_shorten_valid_url_returns_code(client):
    response = client.post("/shorten", json={"url": "https://example.com/long/path"})

    assert response.status_code == 201
    data = response.json()
    assert data["code"]
    assert data["short_url"].endswith(data["code"])
    assert data["original_url"] == "https://example.com/long/path"


def test_shorten_duplicate_url_is_idempotent(client):
    payload = {"url": "https://example.com/same-path"}

    first = client.post("/shorten", json=payload)
    second = client.post("/shorten", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["code"] == second.json()["code"]


def test_shorten_normalizes_scheme_and_host(client):
    first = client.post("/shorten", json={"url": "https://Example.com/page"})
    second = client.post("/shorten", json={"url": "HTTPS://example.com/page"})

    assert first.json()["code"] == second.json()["code"]


def test_shorten_invalid_url_returns_400(client):
    response = client.post("/shorten", json={"url": "not-a-url"})

    assert response.status_code == 400


def test_shorten_rejects_non_http_scheme(client):
    response = client.post("/shorten", json={"url": "ftp://example.com/file"})

    assert response.status_code == 400


def test_different_urls_get_different_codes(client):
    first = client.post("/shorten", json={"url": "https://example.com/one"})
    second = client.post("/shorten", json={"url": "https://example.com/two"})

    assert first.json()["code"] != second.json()["code"]
