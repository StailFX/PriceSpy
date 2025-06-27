import pytest
from PriceSpy.models import Product, Competitor, PriceRecord, metadata
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Настройка in-memory БД для теста моделей
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(bind=engine)

@ pytest.fixture(scope="module")
def tables():
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)

def test_product_table_columns(tables):
    # Проверяем, что таблица Products существует и имеет нужные колонки
    inspector = engine.dialect.get_inspector(engine)
    cols = [c['name'] for c in inspector.get_columns('products')]
    assert 'id' in cols
    assert 'name' in cols
    assert 'created_at' in cols

def test_price_record_relationship(tables):
    session = SessionLocal()
    # создаём объекты
    prod = Product(name='P')
    comp = Competitor(name='C')
    session.add_all([prod, comp])
    session.commit()

    rec = PriceRecord(product_id=prod.id, competitor_id=comp.id, price=5.0, url='u', date='2025-01-01')
    session.add(rec)
    session.commit()

    fetched = session.query(PriceRecord).first()
    assert fetched.product.id == prod.id
    assert fetched.competitor.name == 'C'