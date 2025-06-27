import pytest
from PriceSpy.schemas import ProductCreate, PriceRecordCreate
from pydantic import ValidationError

@pytest.mark.parametrize('name', ['A', 'Test', None, ''])
def test_productcreate_name_validation(name):
    if not name:
        with pytest.raises(ValidationError):
            ProductCreate(name=name)
    else:
        p = ProductCreate(name=name)
        assert p.name == name

def test_price_record_create_types():
    payload = {
        'product_id': 1,
        'competitor_id': 2,
        'price': 12.34,
        'url': 'http://x',
        'date': '2025-06-27'
    }
    pr = PriceRecordCreate(**payload)
    assert isinstance(pr.price, float)
    assert pr.url.startswith('http')