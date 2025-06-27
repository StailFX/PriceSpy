import pytest
from PriceSpy.crud import create_product, get_products, delete_product
from PriceSpy.models import metadata
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)

@pytest.fixture(scope='module', autouse=True)
def setup_db():
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)

@pytest.fixture()
def db():
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

def test_create_and_get_products(db):
    # создаём
    prod = create_product(db, 'New')
    assert prod.id is not None
    # получаем список
    all_ = get_products(db)
    assert any(p.id == prod.id for p in all_)

def test_delete_product(db):
    # создаём
    prod = create_product(db, 'ToDelete')
    pid = prod.id
    # удаляем
    delete_product(db, pid)
    remaining = get_products(db)
    assert not any(p.id == pid for p in remaining)