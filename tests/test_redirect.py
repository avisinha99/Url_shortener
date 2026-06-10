def test_redirect_known_code(client):
    create_response = client.post("/shorten", json={"url": "https://example.com/target"})
    code = create_response.json()["code"]

    response = client.get(f"/{code}", follow_redirects=False)

    assert response.status_code == 301
    assert response.headers["location"] == "https://example.com/target"


def test_redirect_unknown_code_returns_404(client):
    response = client.get("/does-not-exist", follow_redirects=False)

    assert response.status_code == 404
    assert response.json()["detail"] == "Short code not found"
