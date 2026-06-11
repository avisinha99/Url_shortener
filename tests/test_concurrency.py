import concurrent.futures

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db import Base
from app.services.shorten import AliasConflictError, shorten_url


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield factory
    Base.metadata.drop_all(bind=engine)


def test_concurrent_same_url_produces_one_code(session_factory):
    url = "https://example.com/concurrent-same-url"

    def shorten_once():
        db = session_factory()
        try:
            link = shorten_url(db, url)
            return link.code
        finally:
            db.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        codes = list(executor.map(lambda _: shorten_once(), range(8)))

    assert len(set(codes)) == 1


def test_concurrent_alias_conflict_returns_error_not_crash(session_factory):
    db = session_factory()
    shorten_url(db, "https://example.com/first", alias="race-alias")
    db.close()

    def claim_alias(target_url: str):
        db = session_factory()
        try:
            shorten_url(db, target_url, alias="race-alias")
            return "created"
        except AliasConflictError:
            return "conflict"
        finally:
            db.close()

    urls = [f"https://example.com/target-{i}" for i in range(8)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(claim_alias, urls))

    assert results.count("conflict") == 8
