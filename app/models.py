"""資料庫 ORM 模型（SQLite）。

ER 關係：
    City 1 ── * Town
    City 1 ── * Attraction * ── 1 Town
    Attraction * ── * Category          (attraction_categories)
    Attraction 1 ── * AttractionImage
    Attraction 1 ── * Review
    Trip 1 ── * TripItem * ── 1 Attraction
"""
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

attraction_categories = Table(
    "attraction_categories",
    Base.metadata,
    Column("attraction_id", ForeignKey("attractions.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Meta(Base):
    """匯入資訊（資料來源、更新時間等）的 key-value 表。"""

    __tablename__ = "meta"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(Text)

    attractions: Mapped[list["Attraction"]] = relationship(
        secondary=attraction_categories, back_populates="categories"
    )


class City(Base):
    __tablename__ = "cities"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(20), unique=True)

    towns: Mapped[list["Town"]] = relationship(back_populates="city", cascade="all, delete-orphan")


class Town(Base):
    __tablename__ = "towns"

    code: Mapped[str] = mapped_column(String(12), primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    city_code: Mapped[str] = mapped_column(ForeignKey("cities.code", ondelete="CASCADE"), index=True)

    city: Mapped[City] = relationship(back_populates="towns")


class Attraction(TimestampMixin, Base):
    __tablename__ = "attractions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    alternate_names: Mapped[list[str]] = mapped_column(JSON, default=list)

    latitude: Mapped[float | None] = mapped_column(Float, index=True)
    longitude: Mapped[float | None] = mapped_column(Float, index=True)

    city_code: Mapped[str | None] = mapped_column(
        ForeignKey("cities.code", ondelete="SET NULL"), index=True
    )
    town_code: Mapped[str | None] = mapped_column(
        ForeignKey("towns.code", ondelete="SET NULL"), index=True
    )
    zip_code: Mapped[str | None] = mapped_column(String(10))
    street_address: Mapped[str | None] = mapped_column(String(300))

    telephones: Mapped[list[str]] = mapped_column(JSON, default=list)
    website_url: Mapped[str | None] = mapped_column(String(500))
    service_time_info: Mapped[str | None] = mapped_column(Text)
    traffic_info: Mapped[str | None] = mapped_column(Text)
    parking_info: Mapped[str | None] = mapped_column(Text)
    fee_info: Mapped[str | None] = mapped_column(Text)

    service_status: Mapped[int] = mapped_column(Integer, default=1, index=True)
    is_public_access: Mapped[bool] = mapped_column(Boolean, default=True)
    is_free: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    visit_duration: Mapped[int | None] = mapped_column(Integer)  # 建議停留時間（分鐘）
    assets_class: Mapped[int | None] = mapped_column(Integer)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    remarks: Mapped[str | None] = mapped_column(Text)
    source_update_time: Mapped[str | None] = mapped_column(String(40))  # 原始資料更新時間

    city: Mapped[City | None] = relationship(lazy="joined")
    town: Mapped[Town | None] = relationship(lazy="joined")
    categories: Mapped[list[Category]] = relationship(
        secondary=attraction_categories, back_populates="attractions", lazy="selectin"
    )
    images: Mapped[list["AttractionImage"]] = relationship(
        back_populates="attraction",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AttractionImage.id",
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="attraction", cascade="all, delete-orphan", passive_deletes=True
    )


class AttractionImage(Base):
    __tablename__ = "attraction_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attraction_id: Mapped[str] = mapped_column(
        ForeignKey("attractions.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000))

    attraction: Mapped[Attraction] = relationship(back_populates="images")


class Review(TimestampMixin, Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attraction_id: Mapped[str] = mapped_column(
        ForeignKey("attractions.id", ondelete="CASCADE"), index=True
    )
    author: Mapped[str] = mapped_column(String(50))
    rating: Mapped[int] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(String(100))
    content: Mapped[str | None] = mapped_column(Text)
    visit_date: Mapped[date | None] = mapped_column(Date)

    attraction: Mapped[Attraction] = relationship(back_populates="reviews")


class Trip(TimestampMixin, Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(50))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)

    items: Mapped[list["TripItem"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(TripItem.day, TripItem.sequence, TripItem.id)",
        lazy="selectin",
    )


class TripItem(Base):
    __tablename__ = "trip_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    attraction_id: Mapped[str] = mapped_column(
        ForeignKey("attractions.id", ondelete="CASCADE"), index=True
    )
    day: Mapped[int] = mapped_column(Integer, default=1)
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    note: Mapped[str | None] = mapped_column(String(500))

    trip: Mapped[Trip] = relationship(back_populates="items")
    attraction: Mapped[Attraction] = relationship(lazy="joined")
