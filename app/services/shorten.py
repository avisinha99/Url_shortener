import threading
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Click, Link
from app.services.code_generator import MAX_GENERATION_ATTEMPTS, generate_code
from app.services.url_validator import (
    AliasValidationError,
    UrlValidationError,
    normalize_url,
    validate_alias,
)

_url_locks: dict[str, threading.Lock] = {}
_url_locks_guard = threading.Lock()


class AliasConflictError(Exception):
    pass


class CodeGenerationError(Exception):
    pass


def _lock_for_url(normalized_url: str) -> threading.Lock:
    with _url_locks_guard:
        if normalized_url not in _url_locks:
            _url_locks[normalized_url] = threading.Lock()
        return _url_locks[normalized_url]


def build_short_url(code: str) -> str:
    return f"{settings.base_url.rstrip('/')}/{code}"


def shorten_url(db: Session, url: str | None, alias: str | None = None) -> Link:
    if url is None:
        raise UrlValidationError("URL is required")

    normalized_url = normalize_url(url)

    if alias is None:
        return _shorten_with_generated_code(db, normalized_url)

    return _shorten_with_alias(db, normalized_url, alias)


def _shorten_with_generated_code(db: Session, normalized_url: str) -> Link:
    with _lock_for_url(normalized_url):
        existing = (
            db.query(Link)
            .filter(Link.original_url == normalized_url, Link.is_custom.is_(False))
            .first()
        )
        if existing:
            return existing

        for _ in range(MAX_GENERATION_ATTEMPTS):
            code = generate_code()
            link = Link(code=code, original_url=normalized_url, is_custom=False)
            db.add(link)
            try:
                db.commit()
                db.refresh(link)
                return link
            except IntegrityError:
                db.rollback()

        raise CodeGenerationError("Failed to generate a unique short code")


def _shorten_with_alias(db: Session, normalized_url: str, alias: str) -> Link:
    validated_alias = validate_alias(alias)

    existing_alias = db.query(Link).filter(Link.code == validated_alias).first()
    if existing_alias:
        if existing_alias.original_url == normalized_url:
            return existing_alias
        raise AliasConflictError(f"Alias '{validated_alias}' is already taken")

    link = Link(code=validated_alias, original_url=normalized_url, is_custom=True)
    db.add(link)
    try:
        db.commit()
        db.refresh(link)
        return link
    except IntegrityError:
        db.rollback()
        existing_alias = db.query(Link).filter(Link.code == validated_alias).first()
        if existing_alias and existing_alias.original_url == normalized_url:
            return existing_alias
        raise AliasConflictError(f"Alias '{validated_alias}' is already taken") from None


def get_link_by_code(db: Session, code: str) -> Link | None:
    return db.query(Link).filter(Link.code == code).first()


def record_click(db: Session, link: Link) -> None:
    db.add(Click(link_id=link.id))
    db.commit()


def get_stats(db: Session, code: str) -> dict | None:
    link = get_link_by_code(db, code)
    if link is None:
        return None

    click_count = db.query(func.count(Click.id)).filter(Click.link_id == link.id).scalar()
    last_clicked_at: datetime | None = (
        db.query(func.max(Click.clicked_at)).filter(Click.link_id == link.id).scalar()
    )

    return {
        "code": link.code,
        "original_url": link.original_url,
        "click_count": click_count,
        "created_at": link.created_at,
        "last_clicked_at": last_clicked_at,
    }


__all__ = [
    "AliasConflictError",
    "CodeGenerationError",
    "AliasValidationError",
    "UrlValidationError",
    "build_short_url",
    "shorten_url",
    "get_link_by_code",
    "record_click",
    "get_stats",
]
