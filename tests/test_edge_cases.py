def test_custom_alias_works(client):
    response = client.post(
        "/shorten",
        json={"url": "https://example.com/docs-page", "alias": "my-docs"},
    )

    assert response.status_code == 201
    assert response.json()["code"] == "my-docs"

    redirect = client.get("/my-docs", follow_redirects=False)
    assert redirect.status_code == 301
    assert redirect.headers["location"] == "https://example.com/docs-page"


def test_duplicate_alias_same_url_is_idempotent(client):
    payload = {"url": "https://example.com/page", "alias": "shared-alias"}

    first = client.post("/shorten", json=payload)
    second = client.post("/shorten", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["code"] == second.json()["code"]


def test_duplicate_alias_different_url_returns_409(client):
    client.post("/shorten", json={"url": "https://example.com/a", "alias": "taken"})
    response = client.post("/shorten", json={"url": "https://example.com/b", "alias": "taken"})

    assert response.status_code == 409


def test_invalid_alias_returns_400(client):
    response = client.post(
        "/shorten",
        json={"url": "https://example.com/a", "alias": "bad alias!"},
    )

    assert response.status_code == 400


def test_too_short_alias_returns_400(client):
    response = client.post(
        "/shorten",
        json={"url": "https://example.com/a", "alias": "ab"},
    )

    assert response.status_code == 400


def test_reserved_alias_returns_400(client):
    response = client.post(
        "/shorten",
        json={"url": "https://example.com/a", "alias": "health"},
    )

    assert response.status_code == 400
