import asyncio
import pytest
from starlette.testclient import TestClient
import async_main
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="function")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="function")
def test_client():
    # Backup original
    original_engine = async_main.engine
    original_async_session_maker = async_main.async_session_maker
    original_database_url = async_main.DATABASE_URL

    # Set up test database
    async_main.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    test_engine = create_async_engine(async_main.DATABASE_URL, echo=True)
    async_main.engine = test_engine
    TestAsyncSessionMaker = sessionmaker(
        bind=test_engine, class_=async_main.AsyncSession, expire_on_commit=False
    )
    async_main.async_session_maker = TestAsyncSessionMaker

    # Create tables
    async def create_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(async_main.Base.metadata.create_all)

    # Since we are in a sync fixture, we need to run the async create_tables
    import asyncio
    asyncio.run(create_tables())

    # Create test client
    client = TestClient(async_main.app)
    yield client

    # Teardown: restore original
    async_main.engine = original_engine
    async_main.async_session_maker = original_async_session_maker
    async_main.DATABASE_URL = original_database_url

def test_get_users_empty(test_client):
    response = test_client.get("/users/")
    assert response.status_code == 200
    assert response.json() == []

def test_create_user(test_client):
    response = test_client.post("/users/?email=test@example.com")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_get_users_after_create(test_client):
    # First create a user
    test_client.post("/users/?email=test@example.com")
    
    # Then get users
    response = test_client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "test@example.com"