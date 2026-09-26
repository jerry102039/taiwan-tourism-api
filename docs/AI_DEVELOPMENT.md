# AI 輔助開發紀錄

本專案使用 **Claude Code**（Anthropic 推出的終端機 AI 程式開發工具）進行開發。
以下記錄開發流程、給 AI 的主要指示，以及 AI 協助完成的設計決策。

## 使用工具

| 工具 | 用途 |
|---|---|
| Claude Code (CLI) | 資料分析、API 設計、程式實作、測試撰寫、文件產生 |
| `CLAUDE.md` | 專案層級的 AI 設定檔，描述架構與開發規範，讓 AI 每次都遵循一致的慣例 |
| FastAPI 自動文件 | 由程式碼自動產生 OpenAPI 規格與 Swagger UI / ReDoc |
| Newman | 以命令列執行 Postman Collection，驗證組態檔可正確運作 |

## 開發流程

### 1. 選擇與分析 Open Data
**Prompt：**
> 我現在有一個作業是要用政府開放資料去做一個 FastAPI 伺服器……老師說做得越完整分數越高。（附上作業說明）

AI 的處理步驟：
1. 透過 `data.gov.tw` 的 API（`/api/v2/rest/dataset/7777`）查詢資料集的下載網址
2. 下載 `Attraction-json.zip` 並解壓，發現內含 `AttractionList.json`（景點主檔，6,226 筆）
3. 以 Python 分析欄位分佈：縣市 22 個、鄉鎮 348 個、圖片 10,725 張、類型代碼 28 種
4. 下載《觀光資料標準 V2.1》PDF，擷取 **景點類型代碼 (AttractionClassEnum)**、
   **營運狀態代碼 (ServiceStatusEnum)**、**文化資產級別代碼 (AssetsClassEnum)** 對照表，寫入 `app/enums.py`

**選擇此資料集的理由（AI 建議）：**
- 資料量適中（6 千多筆）、欄位豐富（座標、地址、圖片、類型、標籤）
- 內含可正規化的關聯（縣市 → 鄉鎮 → 景點、景點 ↔ 類型、景點 → 圖片），適合設計多個 Resource
- 有經緯度，可延伸地理查詢功能

### 2. 設計 RESTful API
AI 依據資料特性提出的 Resource 設計：

| 設計 | 理由 |
|---|---|
| 把巢狀 JSON 正規化成 `cities` / `towns` / `categories` / `attractions` / `images` | 原始資料每筆景點都重複存縣市、鄉鎮名稱；正規化後每個實體都可以獨立 CRUD |
| `images` 設計為 `attractions/{id}/images` 子資源 | 圖片必定屬於某景點，巢狀路徑能表達從屬關係 |
| 新增 `reviews` 與 `trips` 資源 | 讓 API 不只是「資料查詢」，而能支援實際應用（評分、行程規劃） |
| `reviews` 同時提供扁平 `/reviews` 與巢狀 `/attractions/{id}/reviews` | 扁平路徑方便跨景點查詢（例：所有 5 星評論），巢狀路徑方便前端顯示單一景點評論 |
| PUT 與 PATCH 分開 | 依 HTTP 語意：PUT 為整筆取代（未給的欄位重設），PATCH 為部分更新 |
| 刪除縣市 / 鄉鎮仍有景點時回 `409`，需 `?force=true` | 避免誤刪造成大量景點失去行政區資料 |
| `/attractions/nearby` | 利用經緯度：先以方框範圍用索引過濾，再以 Haversine 公式計算實際距離 |
| API Key 保護寫入操作 | 讀取開放給大眾、寫入需授權，符合一般開放資料 API 的做法 |

### 3. 實作
- AI 依 `CLAUDE.md` 的規範產生 `app/` 下的程式碼
- 過程中 AI 自行發現並修正的問題：
  - **中文標籤搜尋失效**：SQLAlchemy 的 JSON 欄位預設以 `ensure_ascii=True` 儲存，中文變成 `\uXXXX`，導致 `tag=賞楓` 查不到。
    修正：在 `create_engine` 設定 `json_serializer=lambda o: json.dumps(o, ensure_ascii=False)`
  - **SQLite 外鍵未生效**：SQLite 預設不檢查外鍵，改以 `PRAGMA foreign_keys=ON` 讓串聯刪除生效
  - **PATCH 把必填欄位設為 null 會造成 500**：新增 `reject_nulls()`，改回傳 422

### 4. 測試與驗證
| 方式 | 結果 |
|---|---|
| `pytest`（`tests/test_api.py`） | 23 passed |
| Python API Client（`client/api_client.py`） | 66 個請求全部符合預期狀態碼 |
| Postman Collection（以 Newman 執行） | 68 requests / 68 assertions 全部通過 |

### 5. 文件產生
- `scripts/export_openapi.py`：匯出 `openapi.json`、`openapi.yaml` 與不需伺服器即可瀏覽的 `index.html`（Swagger UI）
- `client/api_client.py --record`：把實際的 Request / Response 自動寫成 `docs/API_EXAMPLES.md`
- `scripts/generate_postman.py`：產生含測試腳本與變數串接的 Postman Collection

## 心得
AI 工具能快速完成資料探勘、樣板程式碼與測試，但仍需要人判斷「API 要怎麼設計才合理」；
透過 `CLAUDE.md` 明確寫下開發規範（狀態碼、PUT/PATCH 語意、分頁格式），能讓 AI 產出的程式碼風格一致。
