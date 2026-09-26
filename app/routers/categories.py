"""景點類型 (categories)：觀光資料標準 AttractionClassEnum。"""
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.common import (
    PageParams,
    conflict,
    get_or_404,
    make_page,
    page_params,
    paginate,
    reject_nulls,
)
from app.database import get_db
from app.security import require_api_key

router = APIRouter(prefix="/categories", tags=["Categories 景點類型"])


def _count(db: Session, category_id: int) -> int:
    return db.scalar(
        select(func.count())
        .select_from(models.attraction_categories)
        .where(models.attraction_categories.c.category_id == category_id)
    )


def _out(db: Session, c: models.Category) -> schemas.CategoryOut:
    return schemas.CategoryOut(id=c.id, name=c.name, description=c.description, attraction_count=_count(db, c.id))


@router.get("", response_model=schemas.Page[schemas.CategoryOut], summary="列出景點類型")
def list_categories(
    response: Response,
    q: str | None = Query(None, description="名稱關鍵字"),
    params: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    stmt = select(models.Category).order_by(models.Category.id)
    if q:
        stmt = stmt.where(models.Category.name.contains(q))
    total, rows = paginate(db, stmt, params, response)
    return make_page(total, params, [_out(db, c) for c in rows])


@router.get("/{category_id}", response_model=schemas.CategoryOut, summary="取得單一景點類型")
def get_category(category_id: int, db: Session = Depends(get_db)):
    return _out(db, get_or_404(db, models.Category, category_id, "Category"))


@router.post(
    "",
    response_model=schemas.CategoryOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="新增景點類型",
    responses={409: {"model": schemas.Message, "description": "代碼或名稱重複"}},
)
def create_category(body: schemas.CategoryCreate, response: Response, db: Session = Depends(get_db)):
    if body.id is not None and db.get(models.Category, body.id):
        raise conflict(f"Category id {body.id} 已存在")
    if db.scalar(select(models.Category).where(models.Category.name == body.name)):
        raise conflict(f"Category 名稱 '{body.name}' 已存在")
    c = models.Category(**body.model_dump())
    db.add(c)
    db.commit()
    response.headers["Location"] = f"/api/v1/categories/{c.id}"
    return _out(db, c)


def _update(db: Session, category_id: int, data: dict) -> schemas.CategoryOut:
    c = get_or_404(db, models.Category, category_id, "Category")
    if "name" in data and data["name"] != c.name:
        if db.scalar(select(models.Category).where(models.Category.name == data["name"])):
            raise conflict(f"Category 名稱 '{data['name']}' 已存在")
    for k, v in data.items():
        setattr(c, k, v)
    db.commit()
    return _out(db, c)


@router.put(
    "/{category_id}",
    response_model=schemas.CategoryOut,
    dependencies=[Depends(require_api_key)],
    summary="整筆更新景點類型",
)
def replace_category(category_id: int, body: schemas.CategoryBase, db: Session = Depends(get_db)):
    return _update(db, category_id, body.model_dump())


@router.patch(
    "/{category_id}",
    response_model=schemas.CategoryOut,
    dependencies=[Depends(require_api_key)],
    summary="部分更新景點類型",
)
def update_category(category_id: int, body: schemas.CategoryUpdate, db: Session = Depends(get_db)):
    return _update(db, category_id, reject_nulls(body.model_dump(exclude_unset=True), "name"))


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
    summary="刪除景點類型（景點本身不會被刪除，只移除關聯）",
)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, models.Category, category_id, "Category"))
    db.commit()
