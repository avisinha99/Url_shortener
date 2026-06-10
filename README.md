# URL Shortener

A small service that turns long URLs into short codes and redirects visitors to the original link.

Built with FastAPI, SQLAlchemy, and SQLite.

## Prerequisites

- Python 3.11+

## Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

The API is served at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

## Test

```bash
pytest
```

## API

### `POST /shorten`

Create a short code for a URL.

Request body:

```json
{
  "url": "https://example.com/very/long/path",
  "alias": "optional-custom-alias"
}
```

Response (`201 Created`):

```json
{
  "code": "abc12Xy",
  "short_url": "http://localhost:8000/abc12Xy",
  "original_url": "https://example.com/very/long/path"
}
```

| Status | When |
|--------|------|
| `201` | Short code created (or existing one returned) |
| `400` | Invalid URL, invalid alias format, or reserved alias |
| `409` | Custom alias already taken by a different URL |

Example:

```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### `GET /{code}`

Redirect to the original URL with `301 Moved Permanently`. Returns `404` for unknown codes.

```bash
curl -i http://localhost:8000/abc12Xy
```

## Design decisions

### Duplicate URLs (idempotent)

Shortening the same URL twice without a custom alias returns the existing auto-generated code instead of creating a new row. URLs are normalized first (scheme and host lowercased), so `https://Example.com` and `HTTPS://example.com` map to the same code.

### Custom aliases

- Must be 3-32 characters: letters, numbers, `_`, or `-`
- Reserved aliases (`health`, `shorten`, `api`, `docs`, `openapi`, `redoc`) are rejected with `400`
- If an alias already points to the same URL, the existing mapping is returned
- If an alias is already taken by a different URL, the API returns `409 Conflict`

### Short-code generation

Auto codes are 7-character base62 strings (`a-z`, `A-Z`, `0-9`) generated with Python's `secrets` module. Collisions are prevented by:

1. A large key space (62^7 ≈ 3.5 trillion combinations)
2. Cryptographically secure randomness
3. A `UNIQUE` constraint on `code` in the database (the real guarantee)
4. A retry loop (up to 5 attempts) on insert conflict

### URL validation

- Only `http://` and `https://` URLs are accepted
- URLs must include a host and be at most 2048 characters
- Scheme and host are normalized to lowercase before storage

### Redirect status

`GET /{code}` returns `301 Moved Permanently` (the standard for URL shorteners), so clients and browsers can cache the redirect.

## Configuration

Optional environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./url_shortener.db` | Database connection string |
| `BASE_URL` | `http://localhost:8000` | Base URL used to build `short_url` |

## Project structure

```
app/
  main.py              # FastAPI app and routes
  config.py            # Settings (env-configurable)
  db.py                # Engine, session, get_db dependency
  models.py            # Link SQLAlchemy model
  schemas.py           # Request/response models
  services/
    shorten.py         # Core shorten/lookup logic
    code_generator.py  # Random base62 short codes
    url_validator.py   # URL and alias validation
tests/
  conftest.py          # In-memory DB + TestClient fixture
  test_shorten.py
  test_redirect.py
  test_edge_cases.py
```

See [WRITEUP.md](WRITEUP.md) for the design write-up.
