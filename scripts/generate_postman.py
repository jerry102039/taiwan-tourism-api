"""產生 Postman Collection v2.1（postman/Taiwan-Tourism-API.postman_collection.json）。

匯入 Postman 後，可用 Collection Runner 依序執行全部請求，每個請求都附有檢查 Status Code 的測試腳本，
並會自動把新建立資源的 id 存入 collection 變數，供後續請求使用。

用法：python scripts/generate_postman.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "postman" / "Taiwan-Tourism-API.postman_collection.json"

AID = "{{attractionId}}"
SAMPLE = "Attraction_345040000G_000001"

NEW_ATTRACTION = {
    "id": AID,
    "name": "國立臺北商業大學",
    "description": "位於臺北市中正區的商業大學",
    "latitude": 25.0421,
    "longitude": 121.5253,
    "city_code": "63000",
    "town_code": "63000050",
    "zip_code": "100",
    "street_address": "濟南路一段321號",
    "telephones": ["(02)2322-6050"],
    "website_url": "https://www.ntub.edu.tw",
    "is_free": True,
    "tags": ["校園"],
    "category_ids": [1, 12],
}

# (資料夾, 名稱, Method, Path, Body, 預期狀態碼, 要儲存的變數名稱 or None, 選項)
REQUESTS = [
    ("0. System", "Health check", "GET", "/health", None, 200, None, {}),
    ("1. Attractions 景點", "List attractions (分頁)", "GET", "/api/v1/attractions?page=1&page_size=5", None, 200, None, {}),
    ("1. Attractions 景點", "Filter: 臺北市 宗教廟宇類 依名稱排序", "GET", "/api/v1/attractions?city=臺北&category_id=4&sort=name", None, 200, None, {}),
    ("1. Attractions 景點", "Search keyword: 老街", "GET", "/api/v1/attractions?q=老街", None, 200, None, {}),
    ("1. Attractions 景點", "Filter: 免費 + 有標籤 賞楓", "GET", "/api/v1/attractions?tag=賞楓", None, 200, None, {}),
    ("1. Attractions 景點", "Nearby (北商大 2km)", "GET", "/api/v1/attractions/nearby?lat=25.0421&lon=121.5253&radius_km=2&limit=10", None, 200, None, {}),
    ("1. Attractions 景點", "Get attraction", "GET", f"/api/v1/attractions/{SAMPLE}", None, 200, None, {}),
    ("1. Attractions 景點", "Get attraction (404)", "GET", "/api/v1/attractions/NOT_EXIST", None, 404, None, {}),
    ("1. Attractions 景點", "Create attraction without API key (401)", "POST", "/api/v1/attractions", NEW_ATTRACTION, 401, None, {"noauth": True}),
    ("1. Attractions 景點", "Create attraction", "POST", "/api/v1/attractions", NEW_ATTRACTION, 201, None, {}),
    ("1. Attractions 景點", "Create attraction duplicate (409)", "POST", "/api/v1/attractions", NEW_ATTRACTION, 409, None, {}),
    ("1. Attractions 景點", "Create attraction invalid (422)", "POST", "/api/v1/attractions", {"name": "", "latitude": 999}, 422, None, {}),
    ("1. Attractions 景點", "Patch attraction", "PATCH", f"/api/v1/attractions/{AID}", {"visit_duration": 90, "tags": ["校園", "學習"]}, 200, None, {}),
    ("1. Attractions 景點", "Replace attraction (PUT)", "PUT", f"/api/v1/attractions/{AID}",
     {k: v for k, v in NEW_ATTRACTION.items() if k != "id"} | {"name": "國立臺北商業大學（臺北校區）"}, 200, None, {}),
    ("2. Images 景點圖片", "List images", "GET", f"/api/v1/attractions/{AID}/images", None, 200, None, {}),
    ("2. Images 景點圖片", "Create image", "POST", f"/api/v1/attractions/{AID}/images",
     {"url": "https://www.ntub.edu.tw/campus.jpg", "name": "校門口"}, 201, "imageId", {}),
    ("2. Images 景點圖片", "Get image", "GET", f"/api/v1/attractions/{AID}/images/{{{{imageId}}}}", None, 200, None, {}),
    ("2. Images 景點圖片", "Patch image", "PATCH", f"/api/v1/attractions/{AID}/images/{{{{imageId}}}}", {"description": "照片提供：學生"}, 200, None, {}),
    ("2. Images 景點圖片", "Replace image", "PUT", f"/api/v1/attractions/{AID}/images/{{{{imageId}}}}",
     {"url": "https://www.ntub.edu.tw/campus2.jpg", "name": "校園"}, 200, None, {}),
    ("2. Images 景點圖片", "Delete image", "DELETE", f"/api/v1/attractions/{AID}/images/{{{{imageId}}}}", None, 204, None, {}),
    ("3. Reviews 評論", "Create review (nested)", "POST", f"/api/v1/attractions/{AID}/reviews",
     {"author": "小明", "rating": 5, "title": "很棒", "visit_date": "2026-09-20"}, 201, "reviewId", {}),
    ("3. Reviews 評論", "Create review (flat)", "POST", "/api/v1/reviews", {"attraction_id": AID, "author": "小華", "rating": 4}, 201, "reviewId2", {}),
    ("3. Reviews 評論", "Create review invalid rating (422)", "POST", "/api/v1/reviews", {"attraction_id": AID, "author": "x", "rating": 9}, 422, None, {}),
    ("3. Reviews 評論", "List reviews of attraction", "GET", f"/api/v1/attractions/{AID}/reviews", None, 200, None, {}),
    ("3. Reviews 評論", "List reviews (min_rating=4)", "GET", "/api/v1/reviews?min_rating=4&sort=-rating", None, 200, None, {}),
    ("3. Reviews 評論", "Get review", "GET", "/api/v1/reviews/{{reviewId}}", None, 200, None, {}),
    ("3. Reviews 評論", "Patch review", "PATCH", "/api/v1/reviews/{{reviewId}}", {"rating": 4}, 200, None, {}),
    ("3. Reviews 評論", "Replace review", "PUT", "/api/v1/reviews/{{reviewId}}", {"author": "小明", "rating": 5, "title": "改評論"}, 200, None, {}),
    ("3. Reviews 評論", "Delete review", "DELETE", "/api/v1/reviews/{{reviewId2}}", None, 204, None, {}),
    ("4. Trips 行程", "Create trip (with items)", "POST", "/api/v1/trips",
     {"title": "臺北一日遊", "owner": "小明", "start_date": "2026-10-10", "end_date": "2026-10-10",
      "items": [{"attraction_id": AID, "day": 1, "sequence": 1, "note": "集合"}]}, 201, "tripId", {}),
    ("4. Trips 行程", "List trips", "GET", "/api/v1/trips?owner=小明", None, 200, None, {}),
    ("4. Trips 行程", "Get trip", "GET", "/api/v1/trips/{{tripId}}", None, 200, None, {}),
    ("4. Trips 行程", "Patch trip", "PATCH", "/api/v1/trips/{{tripId}}", {"description": "北商大周邊散步"}, 200, None, {}),
    ("4. Trips 行程", "Patch trip invalid dates (422)", "PATCH", "/api/v1/trips/{{tripId}}", {"end_date": "2026-10-01"}, 422, None, {}),
    ("4. Trips 行程", "Replace trip (PUT)", "PUT", "/api/v1/trips/{{tripId}}",
     {"title": "臺北半日遊", "owner": "小明", "items": [{"attraction_id": AID}]}, 200, None, {}),
    ("5. Trip Items 行程項目", "Create trip item", "POST", "/api/v1/trips/{{tripId}}/items",
     {"attraction_id": SAMPLE, "day": 2, "sequence": 1, "note": "太平山"}, 201, "itemId", {}),
    ("5. Trip Items 行程項目", "List trip items", "GET", "/api/v1/trips/{{tripId}}/items", None, 200, None, {}),
    ("5. Trip Items 行程項目", "Get trip item", "GET", "/api/v1/trips/{{tripId}}/items/{{itemId}}", None, 200, None, {}),
    ("5. Trip Items 行程項目", "Patch trip item", "PATCH", "/api/v1/trips/{{tripId}}/items/{{itemId}}", {"note": "看日出"}, 200, None, {}),
    ("5. Trip Items 行程項目", "Replace trip item", "PUT", "/api/v1/trips/{{tripId}}/items/{{itemId}}",
     {"attraction_id": SAMPLE, "day": 2, "sequence": 2}, 200, None, {}),
    ("5. Trip Items 行程項目", "Delete trip item", "DELETE", "/api/v1/trips/{{tripId}}/items/{{itemId}}", None, 204, None, {}),
    ("5. Trip Items 行程項目", "Delete trip", "DELETE", "/api/v1/trips/{{tripId}}", None, 204, None, {}),
    ("6. Categories 景點類型", "List categories", "GET", "/api/v1/categories?page_size=30", None, 200, None, {}),
    ("6. Categories 景點類型", "Get category", "GET", "/api/v1/categories/16", None, 200, None, {}),
    ("6. Categories 景點類型", "Create category", "POST", "/api/v1/categories", {"id": 900, "name": "校園類", "description": "大專院校"}, 201, None, {}),
    ("6. Categories 景點類型", "Patch category", "PATCH", "/api/v1/categories/900", {"description": "大學校園"}, 200, None, {}),
    ("6. Categories 景點類型", "Replace category", "PUT", "/api/v1/categories/900", {"name": "學校校園類", "description": "各級學校"}, 200, None, {}),
    ("6. Categories 景點類型", "Delete category", "DELETE", "/api/v1/categories/900", None, 204, None, {}),
    ("7. Cities 縣市", "List cities", "GET", "/api/v1/cities", None, 200, None, {}),
    ("7. Cities 縣市", "Get city", "GET", "/api/v1/cities/63000", None, 200, None, {}),
    ("7. Cities 縣市", "List towns of city", "GET", "/api/v1/cities/63000/towns", None, 200, None, {}),
    ("7. Cities 縣市", "Create city", "POST", "/api/v1/cities", {"code": "99001", "name": "示範市"}, 201, None, {}),
    ("7. Cities 縣市", "Patch city", "PATCH", "/api/v1/cities/99001", {"name": "示範新市"}, 200, None, {}),
    ("7. Cities 縣市", "Replace city", "PUT", "/api/v1/cities/99001", {"name": "示範市"}, 200, None, {}),
    ("8. Towns 鄉鎮市區", "Create town", "POST", "/api/v1/towns", {"code": "99001010", "name": "示範區", "city_code": "99001"}, 201, None, {}),
    ("8. Towns 鄉鎮市區", "List towns", "GET", "/api/v1/towns?city_code=99001", None, 200, None, {}),
    ("8. Towns 鄉鎮市區", "Get town", "GET", "/api/v1/towns/99001010", None, 200, None, {}),
    ("8. Towns 鄉鎮市區", "Patch town", "PATCH", "/api/v1/towns/99001010", {"name": "示範新區"}, 200, None, {}),
    ("8. Towns 鄉鎮市區", "Replace town", "PUT", "/api/v1/towns/99001010", {"code": "99001010", "name": "示範區", "city_code": "99001"}, 200, None, {}),
    ("8. Towns 鄉鎮市區", "Delete city in use (409)", "DELETE", "/api/v1/cities/63000", None, 409, None, {}),
    ("8. Towns 鄉鎮市區", "Delete town", "DELETE", "/api/v1/towns/99001010", None, 204, None, {}),
    ("8. Towns 鄉鎮市區", "Delete city", "DELETE", "/api/v1/cities/99001", None, 204, None, {}),
    ("9. Stats 統計", "Overview", "GET", "/api/v1/stats/overview", None, 200, None, {}),
    ("9. Stats 統計", "By city", "GET", "/api/v1/stats/cities", None, 200, None, {}),
    ("9. Stats 統計", "By category", "GET", "/api/v1/stats/categories", None, 200, None, {}),
    ("9. Stats 統計", "Top rated", "GET", "/api/v1/stats/top-rated?limit=5", None, 200, None, {}),
    ("10. Cleanup 清除", "Delete attraction", "DELETE", f"/api/v1/attractions/{AID}", None, 204, None, {}),
    ("10. Cleanup 清除", "Get deleted attraction (404)", "GET", f"/api/v1/attractions/{AID}", None, 404, None, {}),
]


def _url(path: str) -> dict:
    raw = "{{baseUrl}}" + path
    base, _, query = path.partition("?")
    url = {"raw": raw, "host": ["{{baseUrl}}"], "path": [p for p in base.split("/") if p]}
    if query:
        url["query"] = [{"key": k, "value": v} for k, _, v in (kv.partition("=") for kv in query.split("&"))]
    return url


def _item(name, method, path, body, expected, save_as, opts) -> dict:
    tests = [
        f'pm.test("Status code is {expected}", function () {{',
        f"    pm.response.to.have.status({expected});",
        "});",
    ]
    if save_as:
        tests += [f'pm.collectionVariables.set("{save_as}", pm.response.json().id);']
    request = {"method": method, "header": [], "url": _url(path)}
    if body is not None:
        request["header"].append({"key": "Content-Type", "value": "application/json"})
        request["body"] = {"mode": "raw", "raw": json.dumps(body, ensure_ascii=False, indent=2),
                           "options": {"raw": {"language": "json"}}}
    if opts.get("noauth"):
        request["auth"] = {"type": "noauth"}
    return {"name": name, "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": tests}}],
            "request": request}


def build() -> dict:
    folders: dict[str, list] = {}
    for folder, *rest in REQUESTS:
        folders.setdefault(folder, []).append(_item(*rest))
    return {
        "info": {
            "name": "Taiwan Tourism Open Data API",
            "description": "交通部觀光署景點開放資料 RESTful API 測試集。\n"
                           "請先啟動伺服器（uvicorn app.main:app），再以 Collection Runner 依序執行。",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "auth": {"type": "apikey", "apikey": [
            {"key": "key", "value": "X-API-Key", "type": "string"},
            {"key": "value", "value": "{{apiKey}}", "type": "string"},
            {"key": "in", "value": "header", "type": "string"},
        ]},
        "variable": [
            {"key": "baseUrl", "value": "http://127.0.0.1:8000"},
            {"key": "apiKey", "value": "ntub-iot-2026"},
            {"key": "attractionId", "value": "Attraction_POSTMAN_0001"},
            {"key": "imageId", "value": ""},
            {"key": "reviewId", "value": ""},
            {"key": "reviewId2", "value": ""},
            {"key": "tripId", "value": ""},
            {"key": "itemId", "value": ""},
        ],
        "item": [{"name": name, "item": items} for name, items in folders.items()],
    }


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已產生 {len(REQUESTS)} 個請求 → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
