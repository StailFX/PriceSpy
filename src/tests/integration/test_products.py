import pytest

def test_create_and_list_products(client):
    # создаём продукт
    resp = client.post(
        "/products",
        json={"name": "IntegrationItem"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "IntegrationItem"
    product_id = body["id"]

    # список должен содержать новый продукт
    list_resp = client.get("/products")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert any(item['id'] == product_id for item in data)

@pytest.mark.parametrize("bad_name", ["", None])
def test_create_invalid_product(client, bad_name):
    resp = client.post(
        "/products",
        json={"name": bad_name}
    )
    assert resp.status_code == 422  # Unprocessable Entity