import pytest
from app.models import ProductCreate, PriceRecordBase
from pydantic import ValidationError

def test_product_create_valid():
    p = ProductCreate(name="Widget", sku="W123")
    assert p.name == "Widget"
    assert p.sku == "W123"

def test_product_create_missing_name():
    with pytest.raises(ValidationError):
        ProductCreate(sku="X")  # name — обязательное поле

def test_price_record_base_types():
    data = {
        "product_id": 1,
        "competitor_id": 2,
        "price": 99.99,
        "url": "http://example.com",
        "date": "2025-06-27"
    }
    rec = PriceRecordBase(**data)
    assert rec.price == 99.99
    assert rec.date.isoformat() == "2025-06-27"
