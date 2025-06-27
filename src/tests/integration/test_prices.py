import pytest

def test_price_records_flow(client):
    # создаём продукт и конкурента
    prod = client.post("/products", json={"name": "P"}).json()
    comp = client.post("/competitors", json={"name": "C"}).json()

    # добавляем запись цены
    payload = {
        "product_id": prod['id'],
        "competitor_id": comp['id'],
        "price": 10.5,
        "url": "http://example.com",
        "date": "2025-06-27"
    }
    resp = client.post("/prices", json=payload)
    assert resp.status_code == 201
    record = resp.json()
    assert record['price'] == 10.5

    # получаем историю цен
    history = client.get(f"/prices?product_id={prod['id']}")
    assert history.status_code == 200
    data = history.json()
    assert any(r['id'] == record['id'] for r in data)