import re
from urllib.parse import urlparse, urlunparse

MAX_URL_LENGTH = 2048
RESERVED_ALIASES = frozenset({"shorten", "health", "api", "docs", "openapi", "redoc"})
ALIAS_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,32}$")


class UrlValidationError(ValueError):
    pass


class AliasValidationError(ValueError):
    pass


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise UrlValidationError("URL is required")

    if len(url) > MAX_URL_LENGTH:
        raise UrlValidationError(f"URL must be at most {MAX_URL_LENGTH} characters")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UrlValidationError("URL must use http or https")

    if not parsed.netloc:
        raise UrlValidationError("URL must include a valid host")

    normalized = parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower())
    return urlunparse(normalized)


def validate_alias(alias: str) -> str:
    alias = alias.strip()
    if not ALIAS_PATTERN.fullmatch(alias):
        raise AliasValidationError(
            "Alias must be 3-32 characters and contain only letters, numbers, underscores, or hyphens"
        )

    if alias.lower() in RESERVED_ALIASES:
        raise AliasValidationError(f"Alias '{alias}' is reserved")

    return alias
