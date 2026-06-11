from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db, init_db
from app.schemas import ShortenRequest, ShortenResponse, StatsResponse
from app.services.shorten import (
    AliasConflictError,
    AliasValidationError,
    CodeGenerationError,
    UrlValidationError,
    build_short_url,
    get_link_by_code,
    get_stats,
    record_click,
    shorten_url,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="URL Shortener", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/shorten", response_model=ShortenResponse, status_code=status.HTTP_201_CREATED)
def create_short_url(payload: ShortenRequest, db: Session = Depends(get_db)):
    try:
        link = shorten_url(db, payload.url, payload.alias)
    except (UrlValidationError, AliasValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except AliasConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except CodeGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    return ShortenResponse(
        code=link.code,
        short_url=build_short_url(link.code),
        original_url=link.original_url,
    )


# Stats must be declared before /{code} to avoid being matched as a code named "stats"
@app.get("/{code}/stats", response_model=StatsResponse)
def get_link_stats(code: str, db: Session = Depends(get_db)):
    stats = get_stats(db, code)
    if stats is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short code not found")

    return StatsResponse(**stats)


@app.get("/{code}")
def redirect_to_url(code: str, db: Session = Depends(get_db)):
    link = get_link_by_code(db, code)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short code not found")

    record_click(db, link)
    return RedirectResponse(url=link.original_url, status_code=status.HTTP_301_MOVED_PERMANENTLY)
