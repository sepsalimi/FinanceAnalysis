"""Pytest fixtures using an isolated PostgreSQL test database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
import app.models  # noqa: F401

settings = get_settings()
engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    Base.metadata.create_all(bind=engine)
    from app.db.seed_taxonomy import TAXONOMY
    from app.models.taxonomy import Category

    db = TestingSessionLocal()
    for parent_name, children in TAXONOMY.items():
        parent = Category(
            household_id=None,
            name=parent_name,
            category_level=1,
            is_system_seeded=True,
            is_active=True,
        )
        db.add(parent)
        db.flush()
        for child_name in children:
            db.add(
                Category(
                    household_id=None,
                    parent_category_id=parent.id,
                    name=child_name,
                    category_level=2,
                    is_system_seeded=True,
                    is_active=True,
                )
            )
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
