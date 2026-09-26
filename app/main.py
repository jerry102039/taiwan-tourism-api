"""FastAPI 應用程式進入點。

啟動：uvicorn app.main:app --reload
文件：http://127.0.0.1:8000/docs (Swagger UI)、/redoc (ReDoc)
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text

from app.config import API_PREFIX, APP_TITLE, APP_VERSION
from app.database import engine
from app.routers import attractions, categories, regions, reviews, stats, trips
from app.seed import init_db

logging.basicConfig(level=logging.INFO)

DESCRIPTION = """
以 **交通部觀光署「景點 - 觀光資訊資料庫」** 政府開放資料（6,000+ 筆全台景點）為基礎的 RESTful API。

資料來源：<https://data.gov.tw/dataset/7777>（觀光資料標準 V2.1）

### 資源 (Resources)
| Resource | 說明 |
|---|---|
| `attractions` | 景點（支援關鍵字搜尋、多條件篩選、排序、分頁、附近景點查詢） |
| `attractions/{id}/images` | 景點圖片（子資源） |
| `categories` | 景點類型（文化類、生態類…） |
| `cities` / `towns` | 縣市 / 鄉鎮市區 |
| `reviews` | 遊客評論（1~5 星） |
| `trips` / `trips/{id}/items` | 旅遊行程與行程項目 |
| `stats` | 統計資訊（唯讀） |

### 驗證
所有 **讀取 (GET)** 操作公開；**新增 / 修改 / 刪除 (POST / PUT / PATCH / DELETE)** 需在 Header 帶入
`X-API-Key: ntub-iot-2026`（可按右上角 **Authorize** 按鈕設定）。

### 慣例
* 列表回應格式：`{"total", "page", "page_size", "pages", "items"}`，並附 `X-Total-Count` header
* 建立成功回傳 `201 Created` 與 `Location` header；刪除成功回傳 `204 No Content`
* 錯誤格式：`{"detail": "錯誤說明"}`（404 查無資料、409 資料衝突、422 驗證失敗）
"""

TAGS = [
    {"name": "Attractions 景點", "description": "全台觀光景點 CRUD、搜尋與附近查詢"},
    {"name": "Attraction Images 景點圖片", "description": "景點的圖片子資源"},
    {"name": "Categories 景點類型", "description": "觀光資料標準的景點類型代碼"},
    {"name": "Cities 縣市", "description": "縣市行政區"},
    {"name": "Towns 鄉鎮市區", "description": "鄉鎮市區行政區"},
    {"name": "Reviews 評論", "description": "遊客對景點的評論與評分"},
    {"name": "Trips 旅遊行程", "description": "使用者規劃的旅遊行程"},
    {"name": "Trip Items 行程項目", "description": "行程中的每一個景點安排"},
    {"name": "Stats 統計", "description": "彙總統計資訊"},
    {"name": "System 系統", "description": "健康檢查"},
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    result = init_db()
    if result:
        logging.getLogger("app").info("Open data imported: %s", result)
    yield


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=DESCRIPTION,
    openapi_tags=TAGS,
    lifespan=lifespan,
    contact={"name": "NTUB IoT App 作業"},
    license_info={"name": "政府資料開放授權條款－第1版", "url": "https://data.gov.tw/license"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "Location", "X-Process-Time"],
)


@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{(time.perf_counter() - start) * 1000:.1f}ms"
    return response


for r in (
    attractions.router,
    attractions.images_router,
    reviews.nested,
    categories.router,
    regions.cities,
    regions.towns,
    reviews.router,
    trips.router,
    trips.items_router,
    stats.router,
):
    app.include_router(r, prefix=API_PREFIX)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/health", tags=["System 系統"], summary="健康檢查")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "version": APP_VERSION}
