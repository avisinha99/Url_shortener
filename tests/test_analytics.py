def test_stats_start_at_zero(client):
    r = client.post("/shorten", json={"url": "https://example.com/page"})
    code = r.json()["code"]

    stats = client.get(f"/{code}/stats")

    assert stats.status_code == 200
    data = stats.json()
    assert data["code"] == code
    assert data["original_url"] == "https://example.com/page"
    assert data["click_count"] == 0
    assert data["last_clicked_at"] is None


def test_stats_increment_on_each_redirect(client):
    r = client.post("/shorten", json={"url": "https://example.com/counted"})
    code = r.json()["code"]

    client.get(f"/{code}", follow_redirects=False)
    client.get(f"/{code}", follow_redirects=False)
    client.get(f"/{code}", follow_redirects=False)

    stats = client.get(f"/{code}/stats").json()
    assert stats["click_count"] == 3


def test_stats_last_clicked_at_set_after_redirect(client):
    r = client.post("/shorten", json={"url": "https://example.com/ts"})
    code = r.json()["code"]

    client.get(f"/{code}", follow_redirects=False)

    stats = client.get(f"/{code}/stats").json()
    assert stats["last_clicked_at"] is not None


def test_stats_unknown_code_returns_404(client):
    response = client.get("/no-such-code/stats")

    assert response.status_code == 404


def test_clicks_not_recorded_for_unknown_code(client):
    response = client.get("/ghost", follow_redirects=False)

    assert response.status_code == 404


def test_stats_independent_per_link(client):
    a = client.post("/shorten", json={"url": "https://example.com/a"}).json()["code"]
    b = client.post("/shorten", json={"url": "https://example.com/b"}).json()["code"]

    client.get(f"/{a}", follow_redirects=False)
    client.get(f"/{a}", follow_redirects=False)

    assert client.get(f"/{a}/stats").json()["click_count"] == 2
    assert client.get(f"/{b}/stats").json()["click_count"] == 0
