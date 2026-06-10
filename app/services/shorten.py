from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Link
from app.services.code_generator import MAX_GENERATION_ATTEMPTS, generate_code
from app.services.url_validator import (
    AliasValidationError,
    UrlValidationError,
    normalize_url,
    validate_alias,
)


class AliasConflictError(Exception):
    pass


class CodeGenerationError(Exception):
    pass


def build_short_url(code: str) -> str:
    return f"{settings.base_url.rstrip('/')}/{code}"


def shorten_url(db: Session, url: str, alias: str | None = None) -> Link:
    normalized_url = normalize_url(url)

    if alias is None:
        return _shorten_with_generated_code(db, normalized_url)

    return _shorten_with_alias(db, normalized_url, alias)


def _shorten_with_generated_code(db: Session, normalized_url: str) -> Link:
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
    db.commit()
    db.refresh(link)
    return link


def get_link_by_code(db: Session, code: str) -> Link | None:
    return db.query(Link).filter(Link.code == code).first()


__all__ = [
    "AliasConflictError",
    "CodeGenerationError",
    "AliasValidationError",
    "UrlValidationError",
    "build_short_url",
    "shorten_url",
    "get_link_by_code",
]
