"""旅遊行程 (trips) 與行程項目 (trip items)。"""
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.common import (
    PageParams,
    get_or_404,
    make_page,
    not_found,
    page_params,
    paginate,
    reject_nulls,
    trip_item_out,
    trip_out,
    unprocessable,
)
from app.database import get_db
from app.security import require_api_key

router = APIRouter(prefix="/trips", tags=["Trips 旅遊行程"])
items_router = APIRouter(prefix="/trips/{trip_id}/items", tags=["Trip Items 行程項目"])


def _check_attractions(db: Session, ids: set[str]) -> None:
    if not ids:
        return
    found = set(db.scalars(select(models.Attraction.id).where(models.Attraction.id.in_(ids))))
    missing = ids - found
    if missing:
        raise unprocessable(f"Attraction {sorted(missing)} 不存在")


def _check_date_range(t: models.Trip) -> None:
    if t.start_date and t.end_date and t.end_date < t.start_date:
        raise unprocessable("end_date 不可早於 start_date")


def _load(db: Session, trip_id: int) -> models.Trip:
    return get_or_404(db, models.Trip, trip_id, "Trip")


# ---------------------------------------------------------------- trips
@router.get("", response_model=schemas.Page[schemas.TripSummary], summary="列出旅遊行程")
def list_trips(
    response: Response,
    owner: str | None = Query(None, description="建立者"),
    q: str | None = Query(None, description="標題關鍵字"),
    params: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    T = models.Trip
    stmt = select(T).order_by(T.id.desc())
    if owner:
        stmt = stmt.where(T.owner == owner)
    if q:
        stmt = stmt.where(T.title.contains(q))
    total, rows = paginate(db, stmt, params, response)
    items = [
        schemas.TripSummary(
            id=t.id, title=t.title, owner=t.owner, start_date=t.start_date, end_date=t.end_date, item_count=len(t.items)
        )
        for t in rows
    ]
    return make_page(total, params, items)


@router.get("/{trip_id}", response_model=schemas.TripOut, summary="取得行程（含所有行程項目）")
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    return trip_out(_load(db, trip_id))


@router.post(
    "",
    response_model=schemas.TripOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="建立行程（可同時帶入行程項目）",
)
def create_trip(body: schemas.TripCreate, response: Response, db: Session = Depends(get_db)):
    _check_attractions(db, {i.attraction_id for i in body.items})
    t = models.Trip(**body.model_dump(exclude={"items"}))
    t.items = [models.TripItem(**i.model_dump()) for i in body.items]
    db.add(t)
    db.commit()
    db.refresh(t)
    response.headers["Location"] = f"/api/v1/trips/{t.id}"
    return trip_out(t)


@router.put(
    "/{trip_id}",
    response_model=schemas.TripOut,
    dependencies=[Depends(require_api_key)],
    summary="整筆更新行程（行程項目會以 body 內容整批取代）",
)
def replace_trip(trip_id: int, body: schemas.TripCreate, db: Session = Depends(get_db)):
    t = _load(db, trip_id)
    _check_attractions(db, {i.attraction_id for i in body.items})
    for k, v in body.model_dump(exclude={"items"}).items():
        setattr(t, k, v)
    t.items = [models.TripItem(**i.model_dump()) for i in body.items]
    db.commit()
    db.refresh(t)
    return trip_out(t)


@router.patch("/{trip_id}", response_model=schemas.TripOut, dependencies=[Depends(require_api_key)], summary="部分更新行程")
def update_trip(trip_id: int, body: schemas.TripUpdate, db: Session = Depends(get_db)):
    t = _load(db, trip_id)
    for k, v in reject_nulls(body.model_dump(exclude_unset=True), "title").items():
        setattr(t, k, v)
    _check_date_range(t)
    db.commit()
    db.refresh(t)
    return trip_out(t)


@router.delete(
    "/{trip_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_api_key)], summary="刪除行程"
)
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    db.delete(_load(db, trip_id))
    db.commit()


# ---------------------------------------------------------------- items
def _get_item(db: Session, trip_id: int, item_id: int) -> models.TripItem:
    _load(db, trip_id)
    item = db.get(models.TripItem, item_id)
    if item is None or item.trip_id != trip_id:
        raise not_found("TripItem", item_id)
    return item


@items_router.get("", response_model=list[schemas.TripItemOut], summary="列出行程項目")
def list_items(trip_id: int, day: int | None = Query(None, ge=1, description="只列出第幾天"), db: Session = Depends(get_db)):
    items = _load(db, trip_id).items
    return [trip_item_out(i) for i in items if day is None or i.day == day]


@items_router.get("/{item_id}", response_model=schemas.TripItemOut, summary="取得單一行程項目")
def get_item(trip_id: int, item_id: int, db: Session = Depends(get_db)):
    return trip_item_out(_get_item(db, trip_id, item_id))


@items_router.post(
    "",
    response_model=schemas.TripItemOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="新增行程項目（加入一個景點）",
)
def create_item(trip_id: int, body: schemas.TripItemCreate, response: Response, db: Session = Depends(get_db)):
    _load(db, trip_id)
    _check_attractions(db, {body.attraction_id})
    item = models.TripItem(trip_id=trip_id, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    response.headers["Location"] = f"/api/v1/trips/{trip_id}/items/{item.id}"
    return trip_item_out(item)


def _update_item(db: Session, trip_id: int, item_id: int, data: dict) -> schemas.TripItemOut:
    item = _get_item(db, trip_id, item_id)
    if "attraction_id" in data:
        _check_attractions(db, {data["attraction_id"]})
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return trip_item_out(item)


@items_router.put("/{item_id}", response_model=schemas.TripItemOut, dependencies=[Depends(require_api_key)], summary="整筆更新行程項目")
def replace_item(trip_id: int, item_id: int, body: schemas.TripItemCreate, db: Session = Depends(get_db)):
    return _update_item(db, trip_id, item_id, body.model_dump())


@items_router.patch("/{item_id}", response_model=schemas.TripItemOut, dependencies=[Depends(require_api_key)], summary="部分更新行程項目")
def update_item(trip_id: int, item_id: int, body: schemas.TripItemUpdate, db: Session = Depends(get_db)):
    data = reject_nulls(body.model_dump(exclude_unset=True), "attraction_id", "day", "sequence")
    return _update_item(db, trip_id, item_id, data)


@items_router.delete(
    "/{item_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_api_key)], summary="刪除行程項目"
)
def delete_item(trip_id: int, item_id: int, db: Session = Depends(get_db)):
    db.delete(_get_item(db, trip_id, item_id))
    db.commit()
