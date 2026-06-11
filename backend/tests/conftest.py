import os
import shutil
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="enterprise-support-agent-tests-"))
TEST_DATABASE_PATH = TEST_RUNTIME_DIR / "test.db"
TEST_UPLOAD_DIR = TEST_RUNTIME_DIR / "uploads" / "knowledge"
TEST_VECTOR_STORE_PATH = TEST_RUNTIME_DIR / "data" / "knowledge_vector_store.json"

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH.as_posix()}"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "fake"
os.environ["KNOWLEDGE_UPLOAD_DIR"] = str(TEST_UPLOAD_DIR)
os.environ["VECTOR_STORE_PATH"] = str(TEST_VECTOR_STORE_PATH)
os.environ["SECRET_KEY"] = "step35-test-secret-key"

from app.core.config import get_settings
from app.db.base import Base
from app.db.init_db import init_db
from app.db.session import engine
from app.main import create_app
from app.services.embedding_service import get_embedding_provider
from app.services.llm_service import get_llm_client


def _reset_runtime_files() -> None:
    if TEST_DATABASE_PATH.exists():
        TEST_DATABASE_PATH.unlink()

    if TEST_UPLOAD_DIR.parent.exists():
        shutil.rmtree(TEST_UPLOAD_DIR.parent)

    if TEST_VECTOR_STORE_PATH.parent.exists():
        shutil.rmtree(TEST_VECTOR_STORE_PATH.parent)


@pytest.fixture(autouse=True)
def isolated_test_state() -> Iterator[None]:
    get_settings.cache_clear()
    get_llm_client.cache_clear()
    get_embedding_provider.cache_clear()

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    _reset_runtime_files()
    init_db()

    yield

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    _reset_runtime_files()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@example.com",
            "password": "admin123",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def create_ticket(client: TestClient, auth_headers: dict[str, str]) -> Callable[..., dict]:
    def _create_ticket(**overrides: str) -> dict:
        payload = {
            "title": "Payment issue requires review",
            "content": "Customer reports the payment succeeded but the order is still pending.",
            "customer_name": "Alice",
            "customer_email": "alice@example.com",
            "category": "other",
            "priority": "medium",
            "source": "manual",
        }
        payload.update(overrides)
        response = client.post("/api/tickets", json=payload, headers=auth_headers)
        assert response.status_code == 200
        return response.json()

    return _create_ticket
