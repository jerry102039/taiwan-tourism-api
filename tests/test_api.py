"""API 自動化測試：涵蓋每個 Resource 的 CRUD、查詢功能、錯誤處理與驗證。

執行：pytest -v
"""
from tests.conftest import AUTH, SAMPLE_ID

API = "/api/v1"


# ---------------------------------------------------------------- system / auth
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_openapi_docs_available(client):
    assert client.get("/docs").status_code == 200
    spec = client.get("/openapi.json").json()
    assert "/api/v1/attractions" in spec["paths"]


def test_write_requires_api_key(client):
    r = client.post(f"{API}/categories", json={"name": "未授權"})
    assert r.status_code == 401
    r = client.post(f"{API}/categories", json={"name": "未授權"}, headers={"X-API-Key": "wrong"})
    assert r.status_code == 403


# ---------------------------------------------------------------- attractions: read
def test_list_attractions_pagination(client):
    r = client.get(f"{API}/attractions", params={"page": 2, "page_size": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] > 6000
    assert body["page"] == 2 and body["page_size"] == 5 and len(body["items"]) == 5
    assert r.headers["X-Total-Count"] == str(body["total"])


def test_list_attractions_filters(client):
    r = client.get(f"{API}/attractions", params={"city": "台北", "category_id": 4, "page_size": 100})
    items = r.json()["items"]
    assert items
    assert all(i["city"]["name"] == "臺北市" for i in items)
    assert all(any(c["id"] == 4 for c in i["categories"]) for i in items)

    r = client.get(f"{API}/attractions", params={"is_free": True, "page_size": 100})
    assert all(i["is_free"] for i in r.json()["items"])

    r = client.get(f"{API}/attractions", params={"tag": "賞楓"})
    assert r.json()["total"] >= 1


def test_search_keyword_and_sort(client):
    r = client.get(f"{API}/attractions", params={"q": "太平山", "sort": "name"})
    names = [i["name"] for i in r.json()["items"]]
    assert "太平山國家森林遊樂區" in names
    assert names == sorted(names)


def test_get_attraction_detail(client):
    r = client.get(f"{API}/attractions/{SAMPLE_ID}")
    assert r.status_code == 200
    a = r.json()
    assert a["name"] == "太平山國家森林遊樂區"
    assert a["city"]["name"] == "宜蘭縣"
    assert a["images"] and a["categories"]
    assert a["service_status_label"] == "正常營運"


def test_get_attraction_404(client):
    r = client.get(f"{API}/attractions/not-exist")
    assert r.status_code == 404
    assert "不存在" in r.json()["detail"]


def test_nearby(client):
    r = client.get(f"{API}/attractions/nearby", params={"lat": 25.0421, "lon": 121.5253, "radius_km": 2})
    assert r.status_code == 200
    data = r.json()
    assert data
    distances = [d["distance_km"] for d in data]
    assert distances == sorted(distances) and max(distances) <= 2


def test_nearby_validation(client):
    r = client.get(f"{API}/attractions/nearby", params={"lat": 100, "lon": 121})
    assert r.status_code == 422


# ---------------------------------------------------------------- attractions: CRUD
def test_attraction_crud(client):
    payload = {
        "id": "Attraction_TEST_0001",
        "name": "測試景點",
        "description": "pytest 建立",
        "latitude": 25.04,
        "longitude": 121.52,
        "city_code": "63000",
        "town_code": "63000050",
        "street_address": "濟南路一段321號",
        "is_free": True,
        "tags": ["測試"],
        "category_ids": [1, 12],
    }
    # Create
    r = client.post(f"{API}/attractions", json=payload, headers=AUTH)
    assert r.status_code == 201, r.text
    assert r.headers["Location"].endswith("/attractions/Attraction_TEST_0001")
    created = r.json()
    assert created["town"]["name"] == "中正區"
    assert {c["id"] for c in created["categories"]} == {1, 12}

    # Duplicate -> 409
    assert client.post(f"{API}/attractions", json=payload, headers=AUTH).status_code == 409

    # Patch
    r = client.patch(f"{API}/attractions/Attraction_TEST_0001", json={"name": "測試景點2", "category_ids": [5]}, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["name"] == "測試景點2"
    assert [c["id"] for c in r.json()["categories"]] == [5]
    assert r.json()["description"] == "pytest 建立"  # 未傳入的欄位保持不變

    # Put（整筆取代，未提供欄位重設）
    r = client.put(f"{API}/attractions/Attraction_TEST_0001", json={"name": "整筆取代"}, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["description"] is None and r.json()["categories"] == []

    # Delete
    assert client.delete(f"{API}/attractions/Attraction_TEST_0001", headers=AUTH).status_code == 204
    assert client.get(f"{API}/attractions/Attraction_TEST_0001").status_code == 404


def test_attraction_auto_id_and_ref_validation(client):
    r = client.post(f"{API}/attractions", json={"name": "自動 ID"}, headers=AUTH)
    assert r.status_code == 201
    assert r.json()["id"].startswith("Attraction_USER_")
    client.delete(f"{API}/attractions/{r.json()['id']}", headers=AUTH)

    bad = [
        {"name": "x", "city_code": "00000"},
        {"name": "x", "city_code": "63000", "town_code": "65000010"},  # 鄉鎮不屬於該縣市
        {"name": "x", "category_ids": [999]},
        {"name": ""},
        {"name": "x", "latitude": 200},
        {"name": "x", "service_status": 5},
    ]
    for body in bad:
        assert client.post(f"{API}/attractions", json=body, headers=AUTH).status_code == 422, body


def test_patch_null_required_field(client):
    r = client.patch(f"{API}/attractions/{SAMPLE_ID}", json={"name": None}, headers=AUTH)
    assert r.status_code == 422


# ---------------------------------------------------------------- images
def test_image_crud(client):
    base = f"{API}/attractions/{SAMPLE_ID}/images"
    before = len(client.get(base).json())
    r = client.post(base, json={"url": "https://example.com/a.jpg", "name": "測試圖"}, headers=AUTH)
    assert r.status_code == 201
    img_id = r.json()["id"]
    assert len(client.get(base).json()) == before + 1

    r = client.patch(f"{base}/{img_id}", json={"name": "改名"}, headers=AUTH)
    assert r.json()["name"] == "改名" and r.json()["url"] == "https://example.com/a.jpg"
    r = client.put(f"{base}/{img_id}", json={"url": "https://example.com/b.jpg"}, headers=AUTH)
    assert r.json()["url"] == "https://example.com/b.jpg" and r.json()["name"] is None

    assert client.post(base, json={"url": "not-a-url"}, headers=AUTH).status_code == 422
    assert client.delete(f"{base}/{img_id}", headers=AUTH).status_code == 204
    assert client.get(f"{base}/{img_id}").status_code == 404


def test_image_belongs_to_attraction(client):
    imgs = client.get(f"{API}/attractions/{SAMPLE_ID}/images").json()
    other = f"{API}/attractions/Attraction_371020000A_000479/images/{imgs[0]['id']}"
    assert client.get(other).status_code == 404


# ---------------------------------------------------------------- categories
def test_category_crud(client):
    r = client.post(f"{API}/categories", json={"id": 500, "name": "夜景類", "description": "看夜景"}, headers=AUTH)
    assert r.status_code == 201
    assert client.get(f"{API}/categories/500").json()["attraction_count"] == 0
    assert client.post(f"{API}/categories", json={"name": "夜景類"}, headers=AUTH).status_code == 409
    r = client.patch(f"{API}/categories/500", json={"description": "改描述"}, headers=AUTH)
    assert r.json() == {"id": 500, "name": "夜景類", "description": "改描述", "attraction_count": 0}
    r = client.put(f"{API}/categories/500", json={"name": "夜景"}, headers=AUTH)
    assert r.json()["name"] == "夜景" and r.json()["description"] is None
    assert client.delete(f"{API}/categories/500", headers=AUTH).status_code == 204
    assert client.get(f"{API}/categories/500").status_code == 404


# ---------------------------------------------------------------- cities / towns
def test_city_and_town_crud(client):
    assert client.post(f"{API}/cities", json={"code": "99001", "name": "測試市"}, headers=AUTH).status_code == 201
    assert client.post(f"{API}/cities", json={"code": "99001", "name": "重複"}, headers=AUTH).status_code == 409
    r = client.post(f"{API}/towns", json={"code": "99001010", "name": "測試區", "city_code": "99001"}, headers=AUTH)
    assert r.status_code == 201 and r.json()["city_name"] == "測試市"
    assert client.post(f"{API}/towns", json={"code": "99001020", "name": "x", "city_code": "nope"}, headers=AUTH).status_code == 422

    assert client.get(f"{API}/cities/99001").json()["town_count"] == 1
    assert client.patch(f"{API}/cities/99001", json={"name": "測試新市"}, headers=AUTH).json()["name"] == "測試新市"
    assert client.patch(f"{API}/towns/99001010", json={"name": "新區"}, headers=AUTH).json()["name"] == "新區"
    r = client.put(f"{API}/towns/99001010", json={"code": "99001010", "name": "再改", "city_code": "99001"}, headers=AUTH)
    assert r.json()["name"] == "再改"

    # 建一個景點使用此縣市 → 刪除時 409，加 force 才可刪
    client.post(f"{API}/attractions", json={"id": "Attraction_TEST_CITY", "name": "x", "city_code": "99001"}, headers=AUTH)
    assert client.delete(f"{API}/cities/99001", headers=AUTH).status_code == 409
    assert client.delete(f"{API}/cities/99001", params={"force": True}, headers=AUTH).status_code == 204
    assert client.get(f"{API}/towns/99001010").status_code == 404  # 鄉鎮一併刪除
    assert client.get(f"{API}/attractions/Attraction_TEST_CITY").json()["city"] is None
    client.delete(f"{API}/attractions/Attraction_TEST_CITY", headers=AUTH)


def test_city_towns_listing(client):
    towns = client.get(f"{API}/cities/63000/towns").json()
    assert len(towns) == 12 and all(t["city_code"] == "63000" for t in towns)


# ---------------------------------------------------------------- reviews
def test_review_crud(client):
    r = client.post(
        f"{API}/attractions/{SAMPLE_ID}/reviews",
        json={"author": "小明", "rating": 5, "title": "讚", "visit_date": "2026-09-20"},
        headers=AUTH,
    )
    assert r.status_code == 201
    rid = r.json()["id"]
    assert r.json()["attraction_name"] == "太平山國家森林遊樂區"

    r = client.post(f"{API}/reviews", json={"attraction_id": SAMPLE_ID, "author": "小華", "rating": 3}, headers=AUTH)
    rid2 = r.json()["id"]

    detail = client.get(f"{API}/attractions/{SAMPLE_ID}").json()
    assert detail["review_count"] == 2 and detail["average_rating"] == 4.0

    assert client.get(f"{API}/reviews", params={"min_rating": 4}).json()["total"] == 1
    assert client.get(f"{API}/attractions/{SAMPLE_ID}/reviews").json()["total"] == 2

    top = client.get(f"{API}/stats/top-rated").json()
    assert top[0]["id"] == SAMPLE_ID

    assert client.patch(f"{API}/reviews/{rid}", json={"rating": 4}, headers=AUTH).json()["rating"] == 4
    r = client.put(f"{API}/reviews/{rid}", json={"author": "小明", "rating": 2}, headers=AUTH)
    assert r.json()["rating"] == 2 and r.json()["title"] is None

    assert client.post(f"{API}/reviews", json={"attraction_id": SAMPLE_ID, "author": "x", "rating": 6}, headers=AUTH).status_code == 422
    assert client.post(f"{API}/reviews", json={"attraction_id": "nope", "author": "x", "rating": 3}, headers=AUTH).status_code == 422

    for i in (rid, rid2):
        assert client.delete(f"{API}/reviews/{i}", headers=AUTH).status_code == 204
    assert client.get(f"{API}/reviews/{rid}").status_code == 404


# ---------------------------------------------------------------- trips
def test_trip_crud(client):
    body = {
        "title": "宜蘭兩天一夜",
        "owner": "小明",
        "start_date": "2026-10-10",
        "end_date": "2026-10-11",
        "items": [{"attraction_id": SAMPLE_ID, "day": 1, "sequence": 1, "note": "看日出"}],
    }
    r = client.post(f"{API}/trips", json=body, headers=AUTH)
    assert r.status_code == 201
    trip = r.json()
    tid = trip["id"]
    assert trip["item_count"] == 1 and trip["items"][0]["attraction"]["name"] == "太平山國家森林遊樂區"

    # items sub-resource
    r = client.post(f"{API}/trips/{tid}/items", json={"attraction_id": "Attraction_371020000A_000479", "day": 2}, headers=AUTH)
    assert r.status_code == 201
    item_id = r.json()["id"]
    assert len(client.get(f"{API}/trips/{tid}/items", params={"day": 2}).json()) == 1
    assert client.patch(f"{API}/trips/{tid}/items/{item_id}", json={"note": "午餐"}, headers=AUTH).json()["note"] == "午餐"
    r = client.put(f"{API}/trips/{tid}/items/{item_id}", json={"attraction_id": SAMPLE_ID, "day": 2, "sequence": 3}, headers=AUTH)
    assert r.json()["sequence"] == 3 and r.json()["note"] is None
    assert client.delete(f"{API}/trips/{tid}/items/{item_id}", headers=AUTH).status_code == 204
    assert client.get(f"{API}/trips/{tid}/items/{item_id}").status_code == 404

    # trip update
    assert client.patch(f"{API}/trips/{tid}", json={"title": "改標題"}, headers=AUTH).json()["title"] == "改標題"
    assert client.patch(f"{API}/trips/{tid}", json={"end_date": "2026-10-01"}, headers=AUTH).status_code == 422
    r = client.put(f"{API}/trips/{tid}", json={"title": "全部取代", "items": []}, headers=AUTH)
    assert r.json()["item_count"] == 0 and r.json()["owner"] is None

    assert client.get(f"{API}/trips", params={"q": "全部"}).json()["total"] == 1
    assert client.delete(f"{API}/trips/{tid}", headers=AUTH).status_code == 204
    assert client.get(f"{API}/trips/{tid}").status_code == 404


def test_trip_validation(client):
    bad_dates = {"title": "x", "start_date": "2026-10-10", "end_date": "2026-10-01"}
    assert client.post(f"{API}/trips", json=bad_dates, headers=AUTH).status_code == 422
    bad_attr = {"title": "x", "items": [{"attraction_id": "nope"}]}
    assert client.post(f"{API}/trips", json=bad_attr, headers=AUTH).status_code == 422


def test_delete_attraction_cascades(client):
    client.post(f"{API}/attractions", json={"id": "Attraction_TEST_CASCADE", "name": "x"}, headers=AUTH)
    rv = client.post(f"{API}/attractions/Attraction_TEST_CASCADE/reviews", json={"author": "a", "rating": 5}, headers=AUTH).json()
    trip = client.post(
        f"{API}/trips", json={"title": "t", "items": [{"attraction_id": "Attraction_TEST_CASCADE"}]}, headers=AUTH
    ).json()
    assert client.delete(f"{API}/attractions/Attraction_TEST_CASCADE", headers=AUTH).status_code == 204
    assert client.get(f"{API}/reviews/{rv['id']}").status_code == 404
    assert client.get(f"{API}/trips/{trip['id']}").json()["item_count"] == 0
    client.delete(f"{API}/trips/{trip['id']}", headers=AUTH)


# ---------------------------------------------------------------- stats
def test_stats(client):
    ov = client.get(f"{API}/stats/overview").json()
    assert ov["attractions"] > 6000 and ov["cities"] == 22 and ov["categories"] == 28
    cities = client.get(f"{API}/stats/cities").json()
    assert cities[0]["count"] >= cities[-1]["count"]
    cats = client.get(f"{API}/stats/categories").json()
    assert {c["name"] for c in cats} >= {"文化類", "生態類"}
