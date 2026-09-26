"""SQLAlchemy 引擎與 Session 管理。"""
import json
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    # JSON 欄位保留中文原字（預設會轉成 \uXXXX，導致無法用 LIKE 搜尋中文標籤）
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _record):
    # SQLite 預設不檢查外鍵，需每次連線時開啟，才能讓 ON DELETE CASCADE 生效
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
