# CLAUDE.md

本檔提供給 AI 輔助開發工具（Claude Code）的專案說明，AI 每次在此目錄工作時都會先讀取本檔。

## 專案概述
以交通部觀光署「景點 - 觀光資訊資料庫」Open Data（`data/AttractionList.json`，觀光資料標準 V2.1）
為基礎的 FastAPI RESTful API Server。啟動時若 SQLite 為空，會由 `app/seed.py` 自動匯入並正規化。

## 常用指令
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload                 # 啟動伺服器（http://127.0.0.1:8000/docs）
pytest -v                                     # 自動化測試（使用暫存 DB）
python client/api_client.py --record docs/API_EXAMPLES.md   # 端對端測試 + 產生實測範例（需先啟動伺服器）
python scripts/export_openapi.py              # 更新 docs/openapi.json、openapi.yaml、index.html
python scripts/generate_postman.py            # 更新 Postman Collection
python scripts/import_data.py --reset         # 重建資料庫
```

## 架構
- `app/models.py`：SQLAlchemy ORM（cities、towns、categories、attractions、attraction_categories、attraction_images、reviews、trips、trip_items、meta）
- `app/schemas.py`：Pydantic 模型。命名慣例：`XxxCreate`（POST）、`XxxFields`/`XxxCreate`（PUT 整筆）、`XxxUpdate`（PATCH 全部欄位 optional）、`XxxOut`（回應）
- `app/routers/*.py`：每個 Resource 一個 router，全部掛在 `/api/v1` 之下
- `app/common.py`：分頁 (`page_params`, `paginate`, `make_page`)、錯誤 (`not_found`, `conflict`, `unprocessable`)、序列化函式

## 開發規範
- 每個 Resource 都要有完整 CRUD：`GET` 列表 / `GET` 單筆 / `POST` / `PUT` / `PATCH` / `DELETE`
- 列表 API 一律分頁，回傳 `Page[T]` 並加上 `X-Total-Count` header
- 狀態碼：建立 `201` + `Location` header；刪除 `204`；查無 `404`；重複或仍被使用 `409`；驗證 / 參照錯誤 `422`
- 寫入操作一律加上 `dependencies=[Depends(require_api_key)]`
- PATCH 使用 `model_dump(exclude_unset=True)`，並用 `reject_nulls()` 防止必填欄位被設為 null
- SQLite 必須開啟 `PRAGMA foreign_keys=ON`（已在 `database.py` 處理）以支援 ON DELETE CASCADE
- 所有 API 必須有中文 `summary` 以便 Swagger UI 閱讀；程式註解使用繁體中文
- 新增 / 修改 API 後需：補 pytest 測試 → 執行 `pytest` → 重新匯出 OpenAPI 與 Postman Collection
