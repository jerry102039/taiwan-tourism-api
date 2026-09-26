import os
import tempfile
from pathlib import Path

import pytest

# 測試使用獨立的暫存資料庫，不影響 data/tourism.db
_tmp = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DB_FILE"] = str(_tmp)
os.environ["API_KEY"] = "test-key"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

AUTH = {"X-API-Key": "test-key"}
SAMPLE_ID = "Attraction_345040000G_000001"  # 太平山國家森林遊樂區


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
