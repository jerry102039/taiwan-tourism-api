"""行政區：縣市 (cities) 與鄉鎮市區 (towns)。"""
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
    unprocessable,
)
from app.database import get_db
from app.security import require_api_key

cities = APIRouter(prefix="/cities", tags=["Cities 縣市"])
towns = APIRouter(prefix="/towns", tags=["Towns 鄉鎮市區"])

FORCE_QUERY = Query(False, description="若仍有景點使用此行政區，是否強制刪除（景點的行政區欄位會被清空）")


# ---------------------------------------------------------------- helpers
def _city_out(db: Session, c: models.City) -> schemas.CityOut:
    town_count = db.scalar(select(func.count()).where(models.Town.city_code == c.code))
    attraction_count = db.scalar(select(func.count()).where(models.Attraction.city_code == c.code))
    return schemas.CityOut(code=c.code, name=c.name, town_count=town_count, attraction_count=attraction_count)


def _town_out(db: Session, t: models.Town) -> schemas.TownOut:
    attraction_count = db.scalar(select(func.count()).where(models.Attraction.town_code == t.code))
    return schemas.TownOut(
        code=t.code, name=t.name, city_code=t.city_code, city_name=t.city.name, attraction_count=attraction_count
    )


# ---------------------------------------------------------------- cities
@cities.get("", response_model=schemas.Page[schemas.CityOut], summary="列出縣市")
def list_cities(
    response: Response,
    q: str | None = Query(None, description="名稱關鍵字，例如：臺北"),
    params: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    stmt = select(models.City).order_by(models.City.code)
    if q:
        stmt = stmt.where(models.City.name.contains(q))
    total, rows = paginate(db, stmt, params, response)
    return make_page(total, params, [_city_out(db, c) for c in rows])


@cities.get("/{city_code}", response_model=schemas.CityOut, summary="取得單一縣市")
def get_city(city_code: str, db: Session = Depends(get_db)):
    return _city_out(db, get_or_404(db, models.City, city_code, "City"))


@cities.get("/{city_code}/towns", response_model=list[schemas.TownOut], summary="列出縣市底下的鄉鎮市區")
def list_city_towns(city_code: str, db: Session = Depends(get_db)):
    get_or_404(db, models.City, city_code, "City")
    rows = db.scalars(select(models.Town).where(models.Town.city_code == city_code).order_by(models.Town.code))
    return [_town_out(db, t) for t in rows]


@cities.post(
    "",
    response_model=schemas.CityOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="新增縣市",
    responses={409: {"model": schemas.Message}},
)
def create_city(body: schemas.CityCreate, response: Response, db: Session = Depends(get_db)):
    if db.get(models.City, body.code):
        raise conflict(f"City code '{body.code}' 已存在")
    if db.scalar(select(models.City).where(models.City.name == body.name)):
        raise conflict(f"City 名稱 '{body.name}' 已存在")
    c = models.City(**body.model_dump())
    db.add(c)
    db.commit()
    response.headers["Location"] = f"/api/v1/cities/{c.code}"
    return _city_out(db, c)


def _update_city(db: Session, city_code: str, body: schemas.CityUpdate) -> schemas.CityOut:
    c = get_or_404(db, models.City, city_code, "City")
    if body.name != c.name and db.scalar(select(models.City).where(models.City.name == body.name)):
        raise conflict(f"City 名稱 '{body.name}' 已存在")
    c.name = body.name
    db.commit()
    return _city_out(db, c)


@cities.put("/{city_code}", response_model=schemas.CityOut, dependencies=[Depends(require_api_key)], summary="整筆更新縣市")
def replace_city(city_code: str, body: schemas.CityUpdate, db: Session = Depends(get_db)):
    return _update_city(db, city_code, body)


@cities.patch("/{city_code}", response_model=schemas.CityOut, dependencies=[Depends(require_api_key)], summary="部分更新縣市")
def update_city(city_code: str, body: schemas.CityUpdate, db: Session = Depends(get_db)):
    return _update_city(db, city_code, body)


@cities.delete(
    "/{city_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
    summary="刪除縣市（連同其鄉鎮市區）",
    responses={409: {"model": schemas.Message, "description": "仍有景點位於此縣市且未指定 force=true"}},
)
def delete_city(city_code: str, force: bool = FORCE_QUERY, db: Session = Depends(get_db)):
    c = get_or_404(db, models.City, city_code, "City")
    used = db.scalar(select(func.count()).where(models.Attraction.city_code == city_code))
    if used and not force:
        raise conflict(f"仍有 {used} 個景點位於 {c.name}，如要刪除請加上 ?force=true")
    db.delete(c)
    db.commit()


# ---------------------------------------------------------------- towns
@towns.get("", response_model=schemas.Page[schemas.TownOut], summary="列出鄉鎮市區")
def list_towns(
    response: Response,
    city_code: str | None = Query(None, description="依縣市代碼篩選"),
    q: str | None = Query(None, description="名稱關鍵字"),
    params: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    stmt = select(models.Town).order_by(models.Town.code)
    if city_code:
        stmt = stmt.where(models.Town.city_code == city_code)
    if q:
        stmt = stmt.where(models.Town.name.contains(q))
    total, rows = paginate(db, stmt, params, response)
    return make_page(total, params, [_town_out(db, t) for t in rows])


@towns.get("/{town_code}", response_model=schemas.TownOut, summary="取得單一鄉鎮市區")
def get_town(town_code: str, db: Session = Depends(get_db)):
    return _town_out(db, get_or_404(db, models.Town, town_code, "Town"))


@towns.post(
    "",
    response_model=schemas.TownOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="新增鄉鎮市區",
    responses={409: {"model": schemas.Message}},
)
def create_town(body: schemas.TownCreate, response: Response, db: Session = Depends(get_db)):
    if db.get(models.Town, body.code):
        raise conflict(f"Town code '{body.code}' 已存在")
    if not db.get(models.City, body.city_code):
        raise unprocessable(f"City '{body.city_code}' 不存在")
    t = models.Town(**body.model_dump())
    db.add(t)
    db.commit()
    response.headers["Location"] = f"/api/v1/towns/{t.code}"
    return _town_out(db, t)


def _update_town(db: Session, town_code: str, data: dict) -> schemas.TownOut:
    t = get_or_404(db, models.Town, town_code, "Town")
    if "city_code" in data and not db.get(models.City, data["city_code"]):
        raise unprocessable(f"City '{data['city_code']}' 不存在")
    for k, v in data.items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return _town_out(db, t)


@towns.put("/{town_code}", response_model=schemas.TownOut, dependencies=[Depends(require_api_key)], summary="整筆更新鄉鎮市區")
def replace_town(town_code: str, body: schemas.TownCreate, db: Session = Depends(get_db)):
    if body.code != town_code:
        raise unprocessable("Body 中的 code 必須與 URL 相同")
    return _update_town(db, town_code, body.model_dump(exclude={"code"}))


@towns.patch("/{town_code}", response_model=schemas.TownOut, dependencies=[Depends(require_api_key)], summary="部分更新鄉鎮市區")
def update_town(town_code: str, body: schemas.TownUpdate, db: Session = Depends(get_db)):
    return _update_town(db, town_code, reject_nulls(body.model_dump(exclude_unset=True), "name", "city_code"))


@towns.delete(
    "/{town_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
    summary="刪除鄉鎮市區",
    responses={409: {"model": schemas.Message}},
)
def delete_town(town_code: str, force: bool = FORCE_QUERY, db: Session = Depends(get_db)):
    t = get_or_404(db, models.Town, town_code, "Town")
    used = db.scalar(select(func.count()).where(models.Attraction.town_code == town_code))
    if used and not force:
        raise conflict(f"仍有 {used} 個景點位於 {t.name}，如要刪除請加上 ?force=true")
    db.delete(t)
    db.commit()
