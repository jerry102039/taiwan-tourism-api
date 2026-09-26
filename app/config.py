"""應用程式設定（可用環境變數覆寫）。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Open Data 原始資料檔（交通部觀光署「景點 - 觀光資訊資料庫」）
DATA_FILE = Path(os.getenv("DATA_FILE", BASE_DIR / "data" / "AttractionList.json"))

# SQLite 資料庫檔
DB_FILE = Path(os.getenv("DB_FILE", BASE_DIR / "data" / "tourism.db"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_FILE.as_posix()}")

# 寫入操作（POST / PUT / PATCH / DELETE）所需的 API Key；設為空字串即可關閉驗證
API_KEY = os.getenv("API_KEY", "ntub-iot-2026")

APP_TITLE = "Taiwan Tourism Open Data API"
APP_VERSION = "1.0.0"
API_PREFIX = "/api/v1"
