"""API Key 驗證：保護所有會修改資料的操作（POST / PUT / PATCH / DELETE）。"""
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app import config

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="寫入操作需帶入 API Key（預設為 `ntub-iot-2026`，可用環境變數 `API_KEY` 修改）",
)


def require_api_key(api_key: str | None = Security(api_key_header)) -> None:
    expected = config.API_KEY
    if not expected:  # 未設定 API_KEY 時不檢查
        return
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    if not secrets.compare_digest(api_key, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API Key 錯誤")
