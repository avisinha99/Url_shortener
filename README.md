# URL Shortener

A small service that turns long URLs into short codes and redirects visitors to the original link.

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

The API will be available at `http://localhost:8000`.

## Test

```bash
pytest
```

## API (planned)

- `POST /shorten` — accept a URL and return a short code
- `GET /{code}` — redirect (301) to the original URL
