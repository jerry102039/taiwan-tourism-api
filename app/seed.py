"""將 Open Data JSON 檔匯入 SQLite。

原始資料為巢狀 JSON（每筆景點內含地址、電話、圖片、類型代碼…），
匯入時正規化拆成 cities / towns / categories / attractions / attraction_images 等資料表。
"""
import json
import logging
from pathlib import Path

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app import models
from app.config import DATA_FILE
from app.database import Base, SessionLocal, engine
from app.enums import ATTRACTION_CLASSES

log = logging.getLogger(__name__)


def _clean(value):
    """空字串轉為 None。"""
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def load_open_data(path: Path = DATA_FILE) -> dict:
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def import_data(db: Session, raw: dict) -> dict[str, int]:
    cities: dict[str, str] = {}
    towns: dict[str, tuple[str, str]] = {}
    attractions, images, links = [], [], []

    for a in raw["Attractions"]:
        addr = a.get("PostalAddress") or {}
        city_code, town_code = _clean(addr.get("CityCode")), _clean(addr.get("TownCode"))
        if city_code and addr.get("City"):
            cities.setdefault(city_code, addr["City"].strip())
        if town_code and city_code and addr.get("Town"):
            towns.setdefault(town_code, (addr["Town"].strip(), city_code))
        else:
            town_code = None

        attractions.append(
            {
                "id": a["AttractionID"],
                "name": a["AttractionName"].strip(),
                "description": _clean(a.get("Description")),
                "alternate_names": a.get("AlternateNames") or [],
                "latitude": a.get("PositionLat"),
                "longitude": a.get("PositionLon"),
                "city_code": city_code,
                "town_code": town_code,
                "zip_code": _clean(addr.get("ZipCode")),
                "street_address": _clean(addr.get("StreetAddress")),
                "telephones": [t["Tel"] for t in a.get("Telephones") or [] if t.get("Tel")],
                "website_url": _clean(a.get("WebsiteURL")),
                "service_time_info": _clean(a.get("ServiceTimeInfo")),
                "traffic_info": _clean(a.get("TrafficInfo")),
                "parking_info": _clean(a.get("ParkingInfo")),
                "fee_info": _clean(a.get("FeeInfo")),
                "service_status": a.get("ServiceStatus", 1),
                "is_public_access": bool(a.get("IsPublicAccess", 1)),
                "is_free": bool(a.get("IsAccessibleForFree", 0)),
                "visit_duration": a.get("VisitDuration"),
                "assets_class": a.get("AssetsClass"),
                "tags": a.get("Tags") or [],
                "remarks": _clean(a.get("Remarks")),
                "source_update_time": a.get("UpdateTime"),
            }
        )
        for img in a.get("Images") or []:
            if img.get("URL"):
                images.append(
                    {
                        "attraction_id": a["AttractionID"],
                        "name": _clean(img.get("Name")),
                        "description": _clean(img.get("Description")),
                        "url": img["URL"],
                    }
                )
        for cls in set(a.get("AttractionClasses") or []):
            if cls in ATTRACTION_CLASSES:
                links.append({"attraction_id": a["AttractionID"], "category_id": cls})

    db.execute(
        insert(models.Category),
        [{"id": k, "name": n, "description": d} for k, (n, d) in ATTRACTION_CLASSES.items()],
    )
    db.execute(insert(models.City), [{"code": c, "name": n} for c, n in sorted(cities.items())])
    db.execute(
        insert(models.Town),
        [{"code": c, "name": n, "city_code": cc} for c, (n, cc) in sorted(towns.items())],
    )
    db.execute(insert(models.Attraction), attractions)
    db.execute(insert(models.AttractionImage), images)
    db.execute(insert(models.attraction_categories), links)
    db.execute(
        insert(models.Meta),
        [
            {"key": "data_source", "value": "交通部觀光署 景點 - 觀光資訊資料庫 (https://data.gov.tw/dataset/7777)"},
            {"key": "data_update_time", "value": raw.get("UpdateTime")},
        ],
    )
    db.commit()
    return {
        "cities": len(cities),
        "towns": len(towns),
        "categories": len(ATTRACTION_CLASSES),
        "attractions": len(attractions),
        "images": len(images),
        "attraction_categories": len(links),
    }


def init_db(reset: bool = False) -> dict[str, int] | None:
    """建立資料表；若資料庫是空的（或 reset=True）則從 Open Data 檔匯入。"""
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(models.Attraction.id).limit(1)) is not None:
            return None
        log.info("Importing open data from %s", DATA_FILE)
        return import_data(db, load_open_data())
