"""景點 (attractions) 與其子資源：景點圖片 (images)。"""
import math
import uuid
from enum import Enum

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import and_, exists, or_, select
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.common import (
    PageParams,
    attraction_detail,
    attraction_summary,
    conflict,
    get_or_404,
    make_page,
    not_found,
    page_params,
    paginate,
    reject_nulls,
    unprocessable,
)
from app.database import get_db
from app.enums import ServiceStatus
from app.security import require_api_key

router = APIRouter(prefix="/attractions", tags=["Attractions 景點"])
images_router = APIRouter(prefix="/attractions/{attraction_id}/images", tags=["Attraction Images 景點圖片"])

EARTH_RADIUS_KM = 6371.0088


class SortField(str, Enum):
    id = "id"
    name = "name"
    name_desc = "-name"
    updated = "updated_at"
    updated_desc = "-updated_at"
    source_updated = "source_update_time"
    source_updated_desc = "-source_update_time"


SORT_COLUMNS = {
    SortField.id: models.Attraction.id,
    SortField.name: models.Attraction.name,
    SortField.name_desc: models.Attraction.name.desc(),
    SortField.updated: models.Attraction.updated_at,
    SortField.updated_desc: models.Attraction.updated_at.desc(),
    SortField.source_updated: models.Attraction.source_update_time,
    SortField.source_updated_desc: models.Attraction.source_update_time.desc(),
}


def _base_query():
    return select(models.Attraction).options(selectinload(models.Attraction.images))


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _validate_refs(db: Session, data: dict, current: models.Attraction | None = None) -> list[models.Category] | None:
    """檢查縣市 / 鄉鎮 / 類型代碼是否存在且一致；回傳對應的 Category 物件（若有傳入 category_ids）。"""
    city_code = data.get("city_code", current.city_code if current else None)
    town_code = data.get("town_code", current.town_code if current else None)
    if city_code and not db.get(models.City, city_code):
        raise unprocessable(f"City '{city_code}' 不存在")
    if town_code:
        town = db.get(models.Town, town_code)
        if town is None:
            raise unprocessable(f"Town '{town_code}' 不存在")
        if city_code and town.city_code != city_code:
            raise unprocessable(f"Town '{town_code}' 不屬於 City '{city_code}'")
    if "category_ids" not in data or data["category_ids"] is None:
        return None
    ids = set(data["category_ids"])
    cats = db.scalars(select(models.Category).where(models.Category.id.in_(ids))).all()
    missing = ids - {c.id for c in cats}
    if missing:
        raise unprocessable(f"Category {sorted(missing)} 不存在")
    return list(cats)


def _apply(db: Session, a: models.Attraction, data: dict) -> None:
    cats = _validate_refs(db, data, a)
    data.pop("category_ids", None)
    if "service_status" in data and data["service_status"] is not None:
        data["service_status"] = int(data["service_status"])
    for k, v in data.items():
        setattr(a, k, v)
    if cats is not None:
        a.categories = cats


# ---------------------------------------------------------------- attractions
@router.get("", response_model=schemas.Page[schemas.AttractionSummary], summary="查詢景點列表（分頁、篩選、排序）")
def list_attractions(
    response: Response,
    q: str | None = Query(None, description="關鍵字（比對名稱、別名、描述、地址）", examples=["老街"]),
    city_code: str | None = Query(None, description="縣市代碼", examples=["63000"]),
    city: str | None = Query(None, description="縣市名稱（部分比對）", examples=["臺北"]),
    town_code: str | None = Query(None, description="鄉鎮市區代碼"),
    category_id: list[int] | None = Query(None, description="景點類型代碼，可重複帶入（OR 條件）"),
    is_free: bool | None = Query(None, description="是否免費入場"),
    service_status: ServiceStatus | None = Query(None, description="營運狀態"),
    has_image: bool | None = Query(None, description="是否有圖片"),
    tag: str | None = Query(None, description="標籤（完全比對）", examples=["賞楓"]),
    sort: SortField = Query(SortField.id, description="排序欄位，前面加 - 代表遞減"),
    params: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    A = models.Attraction
    stmt = _base_query()
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(A.name.like(like), A.description.like(like), A.street_address.like(like), A.alternate_names.like(like))
        )
    if city_code:
        stmt = stmt.where(A.city_code == city_code)
    if city:
        stmt = stmt.where(A.city.has(models.City.name.contains(city.replace("台", "臺"))))
    if town_code:
        stmt = stmt.where(A.town_code == town_code)
    if category_id:
        stmt = stmt.where(A.categories.any(models.Category.id.in_(category_id)))
    if is_free is not None:
        stmt = stmt.where(A.is_free == is_free)
    if service_status is not None:
        stmt = stmt.where(A.service_status == int(service_status))
    if has_image is not None:
        cond = exists().where(models.AttractionImage.attraction_id == A.id)
        stmt = stmt.where(cond if has_image else ~cond)
    if tag:
        # tags 以 JSON 陣列儲存，用字串比對 "tag"
        stmt = stmt.where(A.tags.like(f'%"{tag}"%'))
    stmt = stmt.order_by(SORT_COLUMNS[sort], A.id)
    total, rows = paginate(db, stmt, params, response)
    return make_page(total, params, [attraction_summary(a) for a in rows])


@router.get("/nearby", response_model=list[schemas.AttractionNearby], summary="查詢附近景點（依距離排序）")
def nearby_attractions(
    lat: float = Query(..., ge=-90, le=90, description="緯度", examples=[25.0421]),
    lon: float = Query(..., ge=-180, le=180, description="經度", examples=[121.5253]),
    radius_km: float = Query(3, gt=0, le=50, description="搜尋半徑（公里）"),
    category_id: int | None = Query(None, description="景點類型代碼"),
    is_free: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    A = models.Attraction
    # 先用經緯度方框縮小範圍（可用索引），再以 Haversine 公式計算實際距離
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.01))
    stmt = _base_query().where(
        and_(A.latitude.between(lat - dlat, lat + dlat), A.longitude.between(lon - dlon, lon + dlon))
    )
    if category_id is not None:
        stmt = stmt.where(A.categories.any(models.Category.id == category_id))
    if is_free is not None:
        stmt = stmt.where(A.is_free == is_free)
    results = []
    for a in db.scalars(stmt).unique():
        d = _haversine(lat, lon, a.latitude, a.longitude)
        if d <= radius_km:
            results.append(
                schemas.AttractionNearby(**attraction_summary(a).model_dump(), distance_km=round(d, 3))
            )
    results.sort(key=lambda r: r.distance_km)
    return results[:limit]


@router.get(
    "/{attraction_id}",
    response_model=schemas.AttractionDetail,
    summary="取得單一景點詳細資料",
    responses={404: {"model": schemas.Message}},
)
def get_attraction(attraction_id: str, db: Session = Depends(get_db)):
    return attraction_detail(db, get_or_404(db, models.Attraction, attraction_id, "Attraction"))


@router.post(
    "",
    response_model=schemas.AttractionDetail,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="新增景點",
    responses={409: {"model": schemas.Message}, 422: {"description": "欄位驗證失敗或參照的代碼不存在"}},
)
def create_attraction(body: schemas.AttractionCreate, response: Response, db: Session = Depends(get_db)):
    data = body.model_dump()
    attraction_id = data.pop("id") or f"Attraction_USER_{uuid.uuid4().hex[:8]}"
    if db.get(models.Attraction, attraction_id):
        raise conflict(f"Attraction '{attraction_id}' 已存在")
    a = models.Attraction(id=attraction_id)
    _apply(db, a, data)
    db.add(a)
    db.commit()
    db.refresh(a)
    response.headers["Location"] = f"/api/v1/attractions/{a.id}"
    return attraction_detail(db, a)


@router.put(
    "/{attraction_id}",
    response_model=schemas.AttractionDetail,
    dependencies=[Depends(require_api_key)],
    summary="整筆更新景點（未提供的欄位會被重設為預設值）",
)
def replace_attraction(attraction_id: str, body: schemas.AttractionFields, db: Session = Depends(get_db)):
    a = get_or_404(db, models.Attraction, attraction_id, "Attraction")
    _apply(db, a, body.model_dump())
    db.commit()
    db.refresh(a)
    return attraction_detail(db, a)


@router.patch(
    "/{attraction_id}",
    response_model=schemas.AttractionDetail,
    dependencies=[Depends(require_api_key)],
    summary="部分更新景點（只更新有傳入的欄位）",
)
def update_attraction(attraction_id: str, body: schemas.AttractionUpdate, db: Session = Depends(get_db)):
    a = get_or_404(db, models.Attraction, attraction_id, "Attraction")
    data = reject_nulls(
        body.model_dump(exclude_unset=True),
        "name", "service_status", "is_public_access", "is_free",
        "alternate_names", "telephones", "tags", "category_ids",
    )  # fmt: skip
    _apply(db, a, data)
    db.commit()
    db.refresh(a)
    return attraction_detail(db, a)


@router.delete(
    "/{attraction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
    summary="刪除景點（連同其圖片、評論、行程項目）",
)
def delete_attraction(attraction_id: str, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, models.Attraction, attraction_id, "Attraction"))
    db.commit()


# ---------------------------------------------------------------- images
def _get_image(db: Session, attraction_id: str, image_id: int) -> models.AttractionImage:
    img = db.get(models.AttractionImage, image_id)
    if img is None or img.attraction_id != attraction_id:
        raise not_found("Image", image_id)
    return img


@images_router.get("", response_model=list[schemas.ImageOut], summary="列出景點的所有圖片")
def list_images(attraction_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, models.Attraction, attraction_id, "Attraction").images


@images_router.get("/{image_id}", response_model=schemas.ImageOut, summary="取得單張圖片")
def get_image(attraction_id: str, image_id: int, db: Session = Depends(get_db)):
    return _get_image(db, attraction_id, image_id)


@images_router.post(
    "",
    response_model=schemas.ImageOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="新增景點圖片",
)
def create_image(attraction_id: str, body: schemas.ImageCreate, response: Response, db: Session = Depends(get_db)):
    get_or_404(db, models.Attraction, attraction_id, "Attraction")
    img = models.AttractionImage(attraction_id=attraction_id, **body.model_dump(mode="json"))
    db.add(img)
    db.commit()
    response.headers["Location"] = f"/api/v1/attractions/{attraction_id}/images/{img.id}"
    return img


def _update_image(db: Session, attraction_id: str, image_id: int, data: dict) -> models.AttractionImage:
    img = _get_image(db, attraction_id, image_id)
    for k, v in data.items():
        setattr(img, k, v)
    db.commit()
    return img


@images_router.put("/{image_id}", response_model=schemas.ImageOut, dependencies=[Depends(require_api_key)], summary="整筆更新圖片")
def replace_image(attraction_id: str, image_id: int, body: schemas.ImageCreate, db: Session = Depends(get_db)):
    return _update_image(db, attraction_id, image_id, body.model_dump(mode="json"))


@images_router.patch("/{image_id}", response_model=schemas.ImageOut, dependencies=[Depends(require_api_key)], summary="部分更新圖片")
def update_image(attraction_id: str, image_id: int, body: schemas.ImageUpdate, db: Session = Depends(get_db)):
    data = reject_nulls(body.model_dump(mode="json", exclude_unset=True), "url")
    return _update_image(db, attraction_id, image_id, data)


@images_router.delete(
    "/{image_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_api_key)], summary="刪除圖片"
)
def delete_image(attraction_id: str, image_id: int, db: Session = Depends(get_db)):
    db.delete(_get_image(db, attraction_id, image_id))
    db.commit()
