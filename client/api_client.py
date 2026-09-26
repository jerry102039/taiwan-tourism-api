"""Taiwan Tourism Open Data API 的 Python Client。

用法：
    # 1. 先啟動伺服器：uvicorn app.main:app
    # 2. 執行完整 CRUD 示範流程，並把每個 Request / Response 輸出成 Markdown：
    python client/api_client.py --base-url http://127.0.0.1:8000 --record docs/API_EXAMPLES.md

也可以在其他程式中 import 使用：
    from client.api_client import TourismAPIClient
    api = TourismAPIClient("http://127.0.0.1:8000", api_key="ntub-iot-2026")
    api.list_attractions(city="臺北", page_size=5)
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import httpx


@dataclass
class Record:
    title: str
    method: str
    url: str
    request_body: Any
    status_code: int
    response_body: Any


@dataclass
class TourismAPIClient:
    base_url: str = "http://127.0.0.1:8000"
    api_key: str | None = "ntub-iot-2026"
    timeout: float = 30.0
    records: list[Record] = field(default_factory=list)

    def __post_init__(self):
        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        self._http = httpx.Client(base_url=self.base_url.rstrip("/"), headers=headers, timeout=self.timeout)
        self._title = ""

    # ------------------------------------------------------------ core
    def request(self, method: str, path: str, *, json_body: Any = None, params: dict | None = None) -> httpx.Response:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        resp = self._http.request(method, path, json=json_body, params=params)
        try:
            body = resp.json() if resp.content else None
        except ValueError:
            body = resp.text
        self.records.append(Record(self._title or f"{method} {path}", method, str(resp.request.url), json_body, resp.status_code, body))
        self._title = ""
        return resp

    def titled(self, title: str) -> TourismAPIClient:
        """為下一個請求設定說明文字（用於產生範例文件）。"""
        self._title = title
        return self

    def close(self):
        self._http.close()

    # ------------------------------------------------------------ attractions
    def list_attractions(self, **params):
        return self.request("GET", "/api/v1/attractions", params=params)

    def nearby_attractions(self, lat: float, lon: float, **params):
        return self.request("GET", "/api/v1/attractions/nearby", params={"lat": lat, "lon": lon, **params})

    def get_attraction(self, attraction_id: str):
        return self.request("GET", f"/api/v1/attractions/{attraction_id}")

    def create_attraction(self, data: dict):
        return self.request("POST", "/api/v1/attractions", json_body=data)

    def replace_attraction(self, attraction_id: str, data: dict):
        return self.request("PUT", f"/api/v1/attractions/{attraction_id}", json_body=data)

    def update_attraction(self, attraction_id: str, data: dict):
        return self.request("PATCH", f"/api/v1/attractions/{attraction_id}", json_body=data)

    def delete_attraction(self, attraction_id: str):
        return self.request("DELETE", f"/api/v1/attractions/{attraction_id}")

    # ------------------------------------------------------------ images
    def list_images(self, attraction_id: str):
        return self.request("GET", f"/api/v1/attractions/{attraction_id}/images")

    def get_image(self, attraction_id: str, image_id: int):
        return self.request("GET", f"/api/v1/attractions/{attraction_id}/images/{image_id}")

    def create_image(self, attraction_id: str, data: dict):
        return self.request("POST", f"/api/v1/attractions/{attraction_id}/images", json_body=data)

    def replace_image(self, attraction_id: str, image_id: int, data: dict):
        return self.request("PUT", f"/api/v1/attractions/{attraction_id}/images/{image_id}", json_body=data)

    def update_image(self, attraction_id: str, image_id: int, data: dict):
        return self.request("PATCH", f"/api/v1/attractions/{attraction_id}/images/{image_id}", json_body=data)

    def delete_image(self, attraction_id: str, image_id: int):
        return self.request("DELETE", f"/api/v1/attractions/{attraction_id}/images/{image_id}")

    # ------------------------------------------------------------ categories
    def list_categories(self, **params):
        return self.request("GET", "/api/v1/categories", params=params)

    def get_category(self, category_id: int):
        return self.request("GET", f"/api/v1/categories/{category_id}")

    def create_category(self, data: dict):
        return self.request("POST", "/api/v1/categories", json_body=data)

    def replace_category(self, category_id: int, data: dict):
        return self.request("PUT", f"/api/v1/categories/{category_id}", json_body=data)

    def update_category(self, category_id: int, data: dict):
        return self.request("PATCH", f"/api/v1/categories/{category_id}", json_body=data)

    def delete_category(self, category_id: int):
        return self.request("DELETE", f"/api/v1/categories/{category_id}")

    # ------------------------------------------------------------ cities / towns
    def list_cities(self, **params):
        return self.request("GET", "/api/v1/cities", params=params)

    def get_city(self, code: str):
        return self.request("GET", f"/api/v1/cities/{code}")

    def list_city_towns(self, code: str):
        return self.request("GET", f"/api/v1/cities/{code}/towns")

    def create_city(self, data: dict):
        return self.request("POST", "/api/v1/cities", json_body=data)

    def replace_city(self, code: str, data: dict):
        return self.request("PUT", f"/api/v1/cities/{code}", json_body=data)

    def update_city(self, code: str, data: dict):
        return self.request("PATCH", f"/api/v1/cities/{code}", json_body=data)

    def delete_city(self, code: str, force: bool = False):
        return self.request("DELETE", f"/api/v1/cities/{code}", params={"force": force or None})

    def list_towns(self, **params):
        return self.request("GET", "/api/v1/towns", params=params)

    def get_town(self, code: str):
        return self.request("GET", f"/api/v1/towns/{code}")

    def create_town(self, data: dict):
        return self.request("POST", "/api/v1/towns", json_body=data)

    def replace_town(self, code: str, data: dict):
        return self.request("PUT", f"/api/v1/towns/{code}", json_body=data)

    def update_town(self, code: str, data: dict):
        return self.request("PATCH", f"/api/v1/towns/{code}", json_body=data)

    def delete_town(self, code: str, force: bool = False):
        return self.request("DELETE", f"/api/v1/towns/{code}", params={"force": force or None})

    # ------------------------------------------------------------ reviews
    def list_reviews(self, **params):
        return self.request("GET", "/api/v1/reviews", params=params)

    def list_attraction_reviews(self, attraction_id: str, **params):
        return self.request("GET", f"/api/v1/attractions/{attraction_id}/reviews", params=params)

    def get_review(self, review_id: int):
        return self.request("GET", f"/api/v1/reviews/{review_id}")

    def create_review(self, data: dict):
        return self.request("POST", "/api/v1/reviews", json_body=data)

    def create_attraction_review(self, attraction_id: str, data: dict):
        return self.request("POST", f"/api/v1/attractions/{attraction_id}/reviews", json_body=data)

    def replace_review(self, review_id: int, data: dict):
        return self.request("PUT", f"/api/v1/reviews/{review_id}", json_body=data)

    def update_review(self, review_id: int, data: dict):
        return self.request("PATCH", f"/api/v1/reviews/{review_id}", json_body=data)

    def delete_review(self, review_id: int):
        return self.request("DELETE", f"/api/v1/reviews/{review_id}")

    # ------------------------------------------------------------ trips
    def list_trips(self, **params):
        return self.request("GET", "/api/v1/trips", params=params)

    def get_trip(self, trip_id: int):
        return self.request("GET", f"/api/v1/trips/{trip_id}")

    def create_trip(self, data: dict):
        return self.request("POST", "/api/v1/trips", json_body=data)

    def replace_trip(self, trip_id: int, data: dict):
        return self.request("PUT", f"/api/v1/trips/{trip_id}", json_body=data)

    def update_trip(self, trip_id: int, data: dict):
        return self.request("PATCH", f"/api/v1/trips/{trip_id}", json_body=data)

    def delete_trip(self, trip_id: int):
        return self.request("DELETE", f"/api/v1/trips/{trip_id}")

    def list_trip_items(self, trip_id: int, **params):
        return self.request("GET", f"/api/v1/trips/{trip_id}/items", params=params)

    def get_trip_item(self, trip_id: int, item_id: int):
        return self.request("GET", f"/api/v1/trips/{trip_id}/items/{item_id}")

    def create_trip_item(self, trip_id: int, data: dict):
        return self.request("POST", f"/api/v1/trips/{trip_id}/items", json_body=data)

    def replace_trip_item(self, trip_id: int, item_id: int, data: dict):
        return self.request("PUT", f"/api/v1/trips/{trip_id}/items/{item_id}", json_body=data)

    def update_trip_item(self, trip_id: int, item_id: int, data: dict):
        return self.request("PATCH", f"/api/v1/trips/{trip_id}/items/{item_id}", json_body=data)

    def delete_trip_item(self, trip_id: int, item_id: int):
        return self.request("DELETE", f"/api/v1/trips/{trip_id}/items/{item_id}")

    # ------------------------------------------------------------ stats
    def stats_overview(self):
        return self.request("GET", "/api/v1/stats/overview")

    def stats_cities(self):
        return self.request("GET", "/api/v1/stats/cities")

    def stats_categories(self):
        return self.request("GET", "/api/v1/stats/categories")

    def stats_top_rated(self, **params):
        return self.request("GET", "/api/v1/stats/top-rated", params=params)


# ====================================================================== demo
class Checker:
    def __init__(self):
        self.passed = self.failed = 0

    def expect(self, resp: httpx.Response, status: int, label: str) -> httpx.Response:
        ok = resp.status_code == status
        self.passed += ok
        self.failed += not ok
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {resp.request.method:6} {resp.request.url.path:55} -> {resp.status_code} (期望 {status})  {label}")
        return resp


def run_demo(api: TourismAPIClient) -> Checker:
    c = Checker()
    sample = "Attraction_345040000G_000001"
    ex = c.expect

    print("\n=== 1. 景點查詢 (Read) ===")
    ex(api.titled("查詢景點列表（分頁）").list_attractions(page=1, page_size=3), 200, "分頁")
    ex(api.titled("多條件篩選：臺北市的宗教廟宇類景點，依名稱排序").list_attractions(city="臺北", category_id=4, sort="name", page_size=3), 200, "篩選")
    ex(api.titled("關鍵字搜尋：老街").list_attractions(q="老街", page_size=3), 200, "搜尋")
    ex(api.titled("取得單一景點詳細資料").get_attraction(sample), 200, "詳細")
    ex(api.titled("查詢北商大附近 1 公里內的景點").nearby_attractions(25.0421, 121.5253, radius_km=1, limit=3), 200, "附近")
    ex(api.titled("查詢不存在的景點（錯誤處理）").get_attraction("Attraction_NOT_EXIST"), 404, "404")

    print("\n=== 2. 景點 CRUD ===")
    new = {
        "id": "Attraction_DEMO_0001",
        "name": "國立臺北商業大學",
        "description": "位於臺北市中正區的商業大學，鄰近華山文創園區。",
        "latitude": 25.0421,
        "longitude": 121.5253,
        "city_code": "63000",
        "town_code": "63000050",
        "zip_code": "100",
        "street_address": "濟南路一段321號",
        "telephones": ["(02)2322-6050"],
        "website_url": "https://www.ntub.edu.tw",
        "is_free": True,
        "tags": ["校園", "學習"],
        "category_ids": [1, 12],
    }
    ex(_without_key(api.titled("未帶 API Key 新增景點（驗證失敗）"), "POST", "/api/v1/attractions", new), 401, "未授權")
    ex(api.titled("新增景點").create_attraction(new), 201, "Create")
    ex(api.titled("重複新增相同 ID（衝突）").create_attraction(new), 409, "409")
    ex(api.titled("新增景點但縣市代碼不存在（驗證失敗）").create_attraction({"name": "錯誤資料", "city_code": "00000"}), 422, "422")
    ex(api.titled("部分更新景點 (PATCH)").update_attraction(new["id"], {"visit_duration": 90, "tags": ["校園", "學習", "資訊"]}), 200, "Patch")
    put_body = {**{k: v for k, v in new.items() if k != "id"}, "name": "國立臺北商業大學（臺北校區）", "service_time_info": "週一至週五 08:00-22:00"}
    ex(api.titled("整筆更新景點 (PUT)").replace_attraction(new["id"], put_body), 200, "Put")

    print("\n=== 3. 景點圖片 CRUD（子資源）===")
    ex(api.titled("列出景點圖片").list_images(new["id"]), 200, "List")
    img = ex(api.titled("新增景點圖片").create_image(new["id"], {"url": "https://www.ntub.edu.tw/images/campus.jpg", "name": "校門口"}), 201, "Create").json()
    ex(api.titled("取得單張圖片").get_image(new["id"], img["id"]), 200, "Read")
    ex(api.titled("部分更新圖片").update_image(new["id"], img["id"], {"description": "照片提供：學生"}), 200, "Patch")
    ex(api.titled("整筆更新圖片").replace_image(new["id"], img["id"], {"url": "https://www.ntub.edu.tw/images/campus2.jpg", "name": "校園"}), 200, "Put")
    ex(api.titled("刪除圖片").delete_image(new["id"], img["id"]), 204, "Delete")

    print("\n=== 4. 評論 CRUD ===")
    r1 = ex(api.titled("為景點新增評論（巢狀路徑）").create_attraction_review(new["id"], {"author": "小明", "rating": 5, "title": "很棒的學校", "content": "交通方便，環境舒適。", "visit_date": "2026-09-20"}), 201, "Create").json()
    r2 = ex(api.titled("新增評論（扁平路徑）").create_review({"attraction_id": new["id"], "author": "小華", "rating": 4, "title": "還不錯"}), 201, "Create").json()
    ex(api.titled("新增評論但評分超出範圍（驗證失敗）").create_review({"attraction_id": new["id"], "author": "x", "rating": 6}), 422, "422")
    ex(api.titled("查詢某景點的評論").list_attraction_reviews(new["id"]), 200, "List")
    ex(api.titled("查詢 4 星以上的評論").list_reviews(min_rating=4, page_size=5), 200, "Filter")
    ex(api.titled("取得單一評論").get_review(r1["id"]), 200, "Read")
    ex(api.titled("部分更新評論").update_review(r2["id"], {"rating": 3, "content": "人有點多"}), 200, "Patch")
    ex(api.titled("整筆更新評論").replace_review(r2["id"], {"author": "小華", "rating": 4, "title": "改觀了"}), 200, "Put")
    ex(api.titled("景點詳細資料（含平均評分）").get_attraction(new["id"]), 200, "Rating")
    ex(api.titled("評價最高的景點").stats_top_rated(limit=3), 200, "Top")

    print("\n=== 5. 行程與行程項目 CRUD ===")
    trip = ex(api.titled("建立行程（同時加入行程項目）").create_trip({
        "title": "臺北一日遊", "owner": "小明", "start_date": "2026-10-10", "end_date": "2026-10-10",
        "items": [{"attraction_id": new["id"], "day": 1, "sequence": 1, "note": "上午集合"}],
    }), 201, "Create").json()
    tid = trip["id"]
    near = api.nearby_attractions(25.0421, 121.5253, radius_km=1, limit=1).json()
    api.records.pop()
    item = ex(api.titled("行程加入景點").create_trip_item(tid, {"attraction_id": near[0]["id"], "day": 1, "sequence": 2, "note": "步行前往"}), 201, "Create").json()
    ex(api.titled("列出行程項目").list_trip_items(tid), 200, "List")
    ex(api.titled("取得單一行程項目").get_trip_item(tid, item["id"]), 200, "Read")
    ex(api.titled("部分更新行程項目").update_trip_item(tid, item["id"], {"note": "午餐後前往"}), 200, "Patch")
    ex(api.titled("整筆更新行程項目").replace_trip_item(tid, item["id"], {"attraction_id": near[0]["id"], "day": 1, "sequence": 3}), 200, "Put")
    ex(api.titled("部分更新行程").update_trip(tid, {"description": "北商大周邊散步"}), 200, "Patch")
    ex(api.titled("行程日期錯誤（驗證失敗）").update_trip(tid, {"end_date": "2026-10-01"}), 422, "422")
    ex(api.titled("取得行程（含項目）").get_trip(tid), 200, "Read")
    ex(api.titled("列出行程").list_trips(owner="小明"), 200, "List")
    ex(api.titled("刪除行程項目").delete_trip_item(tid, item["id"]), 204, "Delete")
    ex(api.titled("整筆更新行程 (PUT)").replace_trip(tid, {"title": "臺北半日遊", "owner": "小明", "items": []}), 200, "Put")
    ex(api.titled("刪除行程").delete_trip(tid), 204, "Delete")

    print("\n=== 6. 景點類型 CRUD ===")
    ex(api.titled("列出景點類型").list_categories(page_size=5), 200, "List")
    ex(api.titled("取得單一景點類型").get_category(16), 200, "Read")
    ex(api.titled("新增景點類型").create_category({"id": 900, "name": "校園類", "description": "大專院校校園"}), 201, "Create")
    ex(api.titled("部分更新景點類型").update_category(900, {"description": "大學與技職校園"}), 200, "Patch")
    ex(api.titled("整筆更新景點類型").replace_category(900, {"name": "學校校園類", "description": "各級學校"}), 200, "Put")
    ex(api.titled("刪除景點類型").delete_category(900), 204, "Delete")

    print("\n=== 7. 縣市 / 鄉鎮 CRUD ===")
    ex(api.titled("列出縣市").list_cities(page_size=5), 200, "List")
    ex(api.titled("取得單一縣市").get_city("63000"), 200, "Read")
    ex(api.titled("列出臺北市的行政區").list_city_towns("63000"), 200, "List")
    ex(api.titled("新增縣市").create_city({"code": "99001", "name": "示範市"}), 201, "Create")
    ex(api.titled("新增鄉鎮市區").create_town({"code": "99001010", "name": "示範區", "city_code": "99001"}), 201, "Create")
    ex(api.titled("查詢鄉鎮市區（依縣市）").list_towns(city_code="99001"), 200, "List")
    ex(api.titled("取得單一鄉鎮市區").get_town("99001010"), 200, "Read")
    ex(api.titled("部分更新鄉鎮市區").update_town("99001010", {"name": "示範新區"}), 200, "Patch")
    ex(api.titled("整筆更新鄉鎮市區").replace_town("99001010", {"code": "99001010", "name": "示範東區", "city_code": "99001"}), 200, "Put")
    ex(api.titled("更新縣市 (PUT)").replace_city("99001", {"name": "示範新市"}), 200, "Put")
    ex(api.titled("刪除仍有景點的縣市（衝突）").delete_city("63000"), 409, "409")
    ex(api.titled("刪除鄉鎮市區").delete_town("99001010"), 204, "Delete")
    ex(api.titled("刪除縣市").delete_city("99001"), 204, "Delete")

    print("\n=== 8. 統計 ===")
    ex(api.titled("資料總覽").stats_overview(), 200, "Overview")
    ex(api.titled("各縣市景點數").stats_cities(), 200, "Cities")
    ex(api.titled("各類型景點數").stats_categories(), 200, "Categories")

    print("\n=== 9. 清除示範資料 ===")
    ex(api.titled("刪除景點（連同評論一併刪除）").delete_attraction(new["id"]), 204, "Delete")
    ex(api.titled("確認景點已刪除").get_attraction(new["id"]), 404, "404")
    ex(api.titled("確認評論已連帶刪除").get_review(r1["id"]), 404, "404")
    return c


def _without_key(api: TourismAPIClient, method: str, path: str, body: Any) -> httpx.Response:
    """不帶 API Key 發送請求，用來示範驗證失敗。"""
    headers = {k: v for k, v in api._http.headers.items() if k.lower() != "x-api-key"}
    with httpx.Client(base_url=api.base_url, headers=headers, timeout=api.timeout) as h:
        resp = h.request(method, path, json=body)
    api.records.append(Record(api._title, method, str(resp.request.url), body, resp.status_code, resp.json()))
    api._title = ""
    return resp


# ====================================================================== markdown
def _truncate(obj: Any, max_items: int = 3, max_str: int = 120) -> Any:
    """縮短過長的列表與字串，讓範例文件易讀。"""
    if isinstance(obj, list):
        out = [_truncate(x, max_items, max_str) for x in obj[:max_items]]
        if len(obj) > max_items:
            out.append(f"...（其餘 {len(obj) - max_items} 筆省略）")
        return out
    if isinstance(obj, dict):
        return {k: _truncate(v, max_items, max_str) for k, v in obj.items()}
    if isinstance(obj, str) and len(obj) > max_str:
        return obj[:max_str] + "…"
    return obj


def write_markdown(records: list[Record], path: Path, base_url: str) -> None:
    lines = [
        "# API 實測範例",
        "",
        f"> 由 `python client/api_client.py --record {path.as_posix()}` 對 `{base_url}` 實際執行後自動產生。",
        "> 長字串與超過 3 筆的陣列已截斷以便閱讀。寫入操作皆帶有 Header `X-API-Key: ntub-iot-2026`。",
        "",
        "| # | 說明 | Method | Path | Status |",
        "|---|---|---|---|---|",
    ]
    for i, r in enumerate(records, 1):
        path_q = unquote(r.url.replace(base_url.rstrip("/"), ""))
        lines.append(f"| {i} | [{r.title}](#{i}) | `{r.method}` | `{path_q}` | {r.status_code} |")
    lines.append("")
    for i, r in enumerate(records, 1):
        path_q = unquote(r.url.replace(base_url.rstrip("/"), ""))
        lines += [f'<a id="{i}"></a>', f"## {i}. {r.title}", "", "**Request**", "", "```http", f"{r.method} {path_q}"]
        if r.request_body is not None:
            lines += ["Content-Type: application/json", "", json.dumps(r.request_body, ensure_ascii=False, indent=2)]
        lines += ["```", "", f"**Response** — Status Code: `{r.status_code}`", ""]
        if r.response_body is None:
            lines += ["（無內容）", ""]
        else:
            body = json.dumps(_truncate(r.response_body), ensure_ascii=False, indent=2)
            lines += ["```json", body, "```", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Taiwan Tourism Open Data API client demo")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default="ntub-iot-2026")
    parser.add_argument("--record", type=Path, help="將所有 Request / Response 輸出為 Markdown 檔")
    args = parser.parse_args(argv)

    api = TourismAPIClient(args.base_url, api_key=args.api_key)
    try:
        checker = run_demo(api)
    except httpx.ConnectError:
        print(f"無法連線到 {args.base_url}，請先啟動伺服器：uvicorn app.main:app")
        return 2
    finally:
        api.close()
    print(f"\n結果：{checker.passed} 通過，{checker.failed} 失敗，共 {checker.passed + checker.failed} 個請求")
    if args.record:
        write_markdown(api.records, args.record, args.base_url)
        print(f"已輸出實測範例：{args.record}")
    return 0 if checker.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
