"""各 Router 共用的工具：分頁、查無資料處理、ORM → Schema 轉換。"""
import math
from dataclasses import dataclass

from fastapi import HTTPException, Query, Response, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.enums import ASSETS_CLASS_LABELS, SERVICE_STATUS_LABELS


@dataclass
class PageParams:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def page_params(
    page: int = Query(1, ge=1, description="頁碼（從 1 開始）"),
    page_size: int = Query(20, ge=1, le=100, description="每頁筆數（1~100）"),
) -> PageParams:
    return PageParams(page, page_size)


def paginate(db: Session, stmt: Select, params: PageParams, response: Response | None = None):
    """執行分頁查詢，回傳 (總筆數, 該頁資料)；並在 Response header 加上 X-Total-Count。"""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = db.scalars(stmt.offset(params.offset).limit(params.page_size)).unique().all()
    if response is not None:
        response.headers["X-Total-Count"] = str(total)
    return total, rows


def make_page(total: int, params: PageParams, items: list) -> dict:
    return {
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "pages": math.ceil(total / params.page_size) if total else 0,
        "items": items,
    }


def not_found(resource: str, key) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} '{key}' 不存在")


def get_or_404(db: Session, model, key, resource: str):
    obj = db.get(model, key)
    if obj is None:
        raise not_found(resource, key)
    return obj


def conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def reject_nulls(data: dict, *required: str) -> dict:
    """PATCH 時不允許把必填欄位設成 null。"""
    bad = [f for f in required if f in data and data[f] is None]
    if bad:
        raise unprocessable(f"欄位 {', '.join(bad)} 不可為 null")
    return data


# ---------------------------------------------------------------- serializers
def attraction_summary(a: models.Attraction) -> schemas.AttractionSummary:
    return schemas.AttractionSummary(
        id=a.id,
        name=a.name,
        city=a.city,
        town=a.town,
        categories=a.categories,
        latitude=a.latitude,
        longitude=a.longitude,
        is_free=a.is_free,
        service_status=a.service_status,
        cover_image=a.images[0].url if a.images else None,
    )


def attraction_detail(db: Session, a: models.Attraction) -> schemas.AttractionDetail:
    count, avg = db.execute(
        select(func.count(models.Review.id), func.avg(models.Review.rating)).where(
            models.Review.attraction_id == a.id
        )
    ).one()
    address_parts = [a.zip_code, a.city.name if a.city else None, a.town.name if a.town else None]
    full_address = "".join(p for p in address_parts if p) + (a.street_address or "")
    data = schemas.AttractionDetail.model_validate(a, from_attributes=True)
    return data.model_copy(
        update={
            "full_address": full_address or None,
            "service_status_label": SERVICE_STATUS_LABELS.get(a.service_status),
            "assets_class_label": ASSETS_CLASS_LABELS.get(a.assets_class) if a.assets_class is not None else None,
            "review_count": count,
            "average_rating": round(avg, 2) if avg is not None else None,
        }
    )


def review_out(r: models.Review) -> schemas.ReviewOut:
    data = schemas.ReviewOut.model_validate(r, from_attributes=True)
    return data.model_copy(update={"attraction_name": r.attraction.name if r.attraction else None})


def trip_item_out(item: models.TripItem) -> schemas.TripItemOut:
    return schemas.TripItemOut(
        id=item.id,
        trip_id=item.trip_id,
        day=item.day,
        sequence=item.sequence,
        note=item.note,
        attraction=attraction_summary(item.attraction),
    )


def trip_out(t: models.Trip) -> schemas.TripOut:
    return schemas.TripOut(
        id=t.id,
        title=t.title,
        description=t.description,
        owner=t.owner,
        start_date=t.start_date,
        end_date=t.end_date,
        item_count=len(t.items),
        items=[trip_item_out(i) for i in t.items],
        created_at=t.created_at,
        updated_at=t.updated_at,
    )
