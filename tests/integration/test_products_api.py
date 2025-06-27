import pytest
from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db

# создаём «in-memory» БД
SQLITE_URL = "sqlite:///:memory:"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# переопределяем зависимость get_db
@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

def test_create_and_get_product(client):
    # создаём
    resp = client.post("/products", json={"name": "Test", "sku": "T001"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Test"
    pid = body["id"]

    # получаем список
    list_resp = client.get("/products")
    assert list_resp.status_code == 200
    products = list_resp.json()
    assert any(p["id"] == pid for p in products)

def test_delete_nonexistent_product(client):
    resp = client.delete("/products/999")
    assert resp.status_code == 404
