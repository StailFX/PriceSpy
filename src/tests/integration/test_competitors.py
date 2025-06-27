import pytest

def test_create_and_get_competitor(client):
    # создаём конкурента
    resp = client.post(
        "/competitors",
        json={"name": "TestComp"}
    )
    assert resp.status_code == 201
    comp = resp.json()
    cid = comp['id']
    assert comp['name'] == 'TestComp'

    # получаем по id
    get_resp = client.get(f"/competitors/{cid}")
    assert get_resp.status_code == 200
    assert get_resp.json()['id'] == cid

def test_list_competitors_pagination(client):
    # создадим несколько
    for i in range(3):
        client.post("/competitors", json={"name": f"Comp{i}"})
    list_resp = client.get("/competitors?skip=1&limit=2")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert len(data) <= 2