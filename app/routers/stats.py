"""統計資訊 (stats)：唯讀的彙總查詢。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.enums import SERVICE_STATUS_LABELS

router = APIRouter(prefix="/stats", tags=["Stats 統計"])


def _count(db: Session, model, *where) -> int:
    return db.scalar(select(func.count()).select_from(model).where(*where))


@router.get("/overview", response_model=schemas.Overview, summary="資料總覽")
def overview(db: Session = Depends(get_db)):
    A = models.Attraction
    status_rows = db.execute(select(A.service_status, func.count()).group_by(A.service_status)).all()
    meta = {m.key: m.value for m in db.scalars(select(models.Meta))}
    return schemas.Overview(
        attractions=_count(db, A),
        free_attractions=_count(db, A, A.is_free.is_(True)),
        attractions_with_images=db.scalar(select(func.count(func.distinct(models.AttractionImage.attraction_id)))),
        cities=_count(db, models.City),
        towns=_count(db, models.Town),
        categories=_count(db, models.Category),
        images=_count(db, models.AttractionImage),
        reviews=_count(db, models.Review),
        trips=_count(db, models.Trip),
        by_service_status=[
            schemas.CountItem(key=str(s), name=SERVICE_STATUS_LABELS.get(s, "未知"), count=c) for s, c in status_rows
        ],
        data_source=meta.get("data_source", ""),
        data_update_time=meta.get("data_update_time"),
    )


@router.get("/cities", response_model=list[schemas.CountItem], summary="各縣市景點數量（由多到少）")
def by_city(db: Session = Depends(get_db)):
    C, A = models.City, models.Attraction
    rows = db.execute(
        select(C.code, C.name, func.count(A.id))
        .join(A, A.city_code == C.code, isouter=True)
        .group_by(C.code)
        .order_by(func.count(A.id).desc(), C.code)
    ).all()
    return [schemas.CountItem(key=code, name=name, count=n) for code, name, n in rows]


@router.get("/categories", response_model=list[schemas.CountItem], summary="各景點類型的景點數量（由多到少）")
def by_category(db: Session = Depends(get_db)):
    C, link = models.Category, models.attraction_categories
    rows = db.execute(
        select(C.id, C.name, func.count(link.c.attraction_id))
        .join(link, link.c.category_id == C.id, isouter=True)
        .group_by(C.id)
        .order_by(func.count(link.c.attraction_id).desc(), C.id)
    ).all()
    return [schemas.CountItem(key=str(i), name=name, count=n) for i, name, n in rows]


@router.get("/top-rated", response_model=list[schemas.RatedAttraction], summary="評價最高的景點")
def top_rated(
    min_reviews: int = Query(1, ge=1, description="至少要有幾則評論"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    A, R = models.Attraction, models.Review
    avg = func.avg(R.rating)
    rows = db.execute(
        select(A.id, A.name, func.count(R.id), avg)
        .join(R, R.attraction_id == A.id)
        .group_by(A.id)
        .having(func.count(R.id) >= min_reviews)
        .order_by(avg.desc(), func.count(R.id).desc())
        .limit(limit)
    ).all()
    return [
        schemas.RatedAttraction(id=i, name=n, review_count=c, average_rating=round(a, 2)) for i, n, c, a in rows
    ]
