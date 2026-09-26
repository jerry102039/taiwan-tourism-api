"""Pydantic 資料模型：定義 API Request / Response 的格式與驗證規則。"""
from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.enums import ServiceStatus

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    """分頁回應格式。"""

    total: int = Field(description="符合條件的總筆數")
    page: int = Field(description="目前頁碼（從 1 開始）")
    page_size: int = Field(description="每頁筆數")
    pages: int = Field(description="總頁數")
    items: list[T]


class Message(BaseModel):
    detail: str


# ---------------------------------------------------------------- Category
class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=50, examples=["夜景類"])
    description: str | None = Field(None, max_length=500, examples=["適合欣賞夜景的地點"])


class CategoryCreate(CategoryBase):
    id: int | None = Field(None, ge=1, le=9999, description="類型代碼；省略時自動編號", examples=[100])


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    description: str | None = Field(None, max_length=500)


class CategoryOut(ORMModel):
    id: int
    name: str
    description: str | None = None
    attraction_count: int = 0


class CategoryRef(ORMModel):
    id: int
    name: str


# ---------------------------------------------------------------- City / Town
class CityCreate(BaseModel):
    code: str = Field(min_length=1, max_length=10, pattern=r"^[0-9A-Za-z]+$", examples=["99001"])
    name: str = Field(min_length=1, max_length=20, examples=["測試市"])


class CityUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=20, examples=["測試新市"])


class CityRef(ORMModel):
    code: str
    name: str


class CityOut(CityRef):
    town_count: int = 0
    attraction_count: int = 0


class TownCreate(BaseModel):
    code: str = Field(min_length=1, max_length=12, pattern=r"^[0-9A-Za-z]+$", examples=["99001010"])
    name: str = Field(min_length=1, max_length=20, examples=["測試區"])
    city_code: str = Field(examples=["99001"])


class TownUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=20)
    city_code: str | None = None


class TownRef(ORMModel):
    code: str
    name: str


class TownOut(TownRef):
    city_code: str
    city_name: str | None = None
    attraction_count: int = 0


# ---------------------------------------------------------------- Image
class ImageCreate(BaseModel):
    url: HttpUrl = Field(examples=["https://example.com/photo.jpg"])
    name: str | None = Field(None, max_length=200, examples=["正門口"])
    description: str | None = Field(None, max_length=500, examples=["照片提供：遊客"])


class ImageUpdate(BaseModel):
    url: HttpUrl | None = None
    name: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=500)


class ImageOut(ORMModel):
    id: int
    attraction_id: str
    url: str
    name: str | None = None
    description: str | None = None


# ---------------------------------------------------------------- Attraction
class AttractionFields(BaseModel):
    """景點共用欄位（PUT 時全部欄位皆會覆寫）。"""

    name: str = Field(min_length=1, max_length=200, examples=["北科大校園"])
    description: str | None = Field(None, examples=["位於臺北市中正區的科技大學"])
    alternate_names: list[str] = Field(default_factory=list, examples=[["臺北商大"]])
    latitude: float | None = Field(None, ge=-90, le=90, examples=[25.0421])
    longitude: float | None = Field(None, ge=-180, le=180, examples=[121.5253])
    city_code: str | None = Field(None, examples=["63000"])
    town_code: str | None = Field(None, examples=["63000050"])
    zip_code: str | None = Field(None, max_length=10, examples=["100"])
    street_address: str | None = Field(None, max_length=300, examples=["濟南路一段321號"])
    telephones: list[str] = Field(default_factory=list, examples=[["(02)2322-6050"]])
    website_url: str | None = Field(None, max_length=500, examples=["https://www.ntub.edu.tw"])
    service_time_info: str | None = Field(None, examples=["週一至週五 08:00-22:00"])
    traffic_info: str | None = None
    parking_info: str | None = None
    fee_info: str | None = None
    service_status: ServiceStatus = Field(
        ServiceStatus.OPEN, description="0 永久停止 / 1 正常營運 / 2 非營運時段 / 3 暫時停止營運 / 9 待確認"
    )
    is_public_access: bool = True
    is_free: bool = Field(False, examples=[True])
    visit_duration: int | None = Field(None, ge=0, le=100000, description="建議停留時間（分鐘）", examples=[60])
    assets_class: int | None = Field(None, description="文化資產級別代碼 (0-5, 9)")
    tags: list[str] = Field(default_factory=list, examples=[["校園", "學習"]])
    remarks: str | None = None
    category_ids: list[int] = Field(default_factory=list, description="景點類型代碼列表", examples=[[1, 12]])


class AttractionCreate(AttractionFields):
    id: str | None = Field(
        None,
        min_length=1,
        max_length=40,
        pattern=r"^[A-Za-z0-9_\-]+$",
        description="景點 ID；省略時自動產生（格式 Attraction_USER_xxxxxxxx）",
    )


class AttractionUpdate(BaseModel):
    """PATCH：只更新有傳入的欄位。"""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    alternate_names: list[str] | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    city_code: str | None = None
    town_code: str | None = None
    zip_code: str | None = Field(None, max_length=10)
    street_address: str | None = Field(None, max_length=300)
    telephones: list[str] | None = None
    website_url: str | None = Field(None, max_length=500)
    service_time_info: str | None = None
    traffic_info: str | None = None
    parking_info: str | None = None
    fee_info: str | None = None
    service_status: ServiceStatus | None = None
    is_public_access: bool | None = None
    is_free: bool | None = None
    visit_duration: int | None = Field(None, ge=0, le=100000)
    assets_class: int | None = None
    tags: list[str] | None = None
    remarks: str | None = None
    category_ids: list[int] | None = None


class AttractionSummary(ORMModel):
    id: str
    name: str
    city: CityRef | None = None
    town: TownRef | None = None
    categories: list[CategoryRef] = []
    latitude: float | None = None
    longitude: float | None = None
    is_free: bool
    service_status: int
    cover_image: str | None = None


class AttractionNearby(AttractionSummary):
    distance_km: float


class AttractionDetail(ORMModel):
    id: str
    name: str
    description: str | None = None
    alternate_names: list[str] = []
    latitude: float | None = None
    longitude: float | None = None
    city: CityRef | None = None
    town: TownRef | None = None
    zip_code: str | None = None
    street_address: str | None = None
    full_address: str | None = None
    telephones: list[str] = []
    website_url: str | None = None
    service_time_info: str | None = None
    traffic_info: str | None = None
    parking_info: str | None = None
    fee_info: str | None = None
    service_status: int
    service_status_label: str | None = None
    is_public_access: bool
    is_free: bool
    visit_duration: int | None = None
    assets_class: int | None = None
    assets_class_label: str | None = None
    tags: list[str] = []
    remarks: str | None = None
    categories: list[CategoryRef] = []
    images: list[ImageOut] = []
    review_count: int = 0
    average_rating: float | None = None
    source_update_time: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ---------------------------------------------------------------- Review
class ReviewFields(BaseModel):
    author: str = Field(min_length=1, max_length=50, examples=["小明"])
    rating: int = Field(ge=1, le=5, description="評分 1~5 顆星", examples=[5])
    title: str | None = Field(None, max_length=100, examples=["風景超美"])
    content: str | None = Field(None, max_length=5000, examples=["步道規劃良好，很適合全家出遊。"])
    visit_date: date | None = Field(None, examples=["2026-09-20"])


class ReviewCreate(ReviewFields):
    attraction_id: str = Field(examples=["Attraction_345040000G_000001"])


class ReviewUpdate(BaseModel):
    author: str | None = Field(None, min_length=1, max_length=50)
    rating: int | None = Field(None, ge=1, le=5)
    title: str | None = Field(None, max_length=100)
    content: str | None = Field(None, max_length=5000)
    visit_date: date | None = None


class ReviewOut(ORMModel):
    id: int
    attraction_id: str
    attraction_name: str | None = None
    author: str
    rating: int
    title: str | None = None
    content: str | None = None
    visit_date: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ---------------------------------------------------------------- Trip
class TripItemCreate(BaseModel):
    attraction_id: str = Field(examples=["Attraction_345040000G_000001"])
    day: int = Field(1, ge=1, le=365, description="第幾天", examples=[1])
    sequence: int = Field(1, ge=1, le=1000, description="當天順序", examples=[1])
    note: str | None = Field(None, max_length=500, examples=["早上出發看日出"])


class TripItemUpdate(BaseModel):
    attraction_id: str | None = None
    day: int | None = Field(None, ge=1, le=365)
    sequence: int | None = Field(None, ge=1, le=1000)
    note: str | None = Field(None, max_length=500)


class TripItemOut(ORMModel):
    id: int
    trip_id: int
    day: int
    sequence: int
    note: str | None = None
    attraction: AttractionSummary


class _DateRangeMixin(BaseModel):
    @model_validator(mode="after")
    def _check_dates(self):
        start, end = getattr(self, "start_date", None), getattr(self, "end_date", None)
        if start and end and end < start:
            raise ValueError("end_date 不可早於 start_date")
        return self


class TripCreate(_DateRangeMixin):
    title: str = Field(min_length=1, max_length=100, examples=["宜蘭兩天一夜"])
    description: str | None = Field(None, examples=["太平山賞楓之旅"])
    owner: str | None = Field(None, max_length=50, examples=["小明"])
    start_date: date | None = Field(None, examples=["2026-10-10"])
    end_date: date | None = Field(None, examples=["2026-10-11"])
    items: list[TripItemCreate] = Field(default_factory=list, description="可同時建立行程項目")


class TripUpdate(_DateRangeMixin):
    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    owner: str | None = Field(None, max_length=50)
    start_date: date | None = None
    end_date: date | None = None


class TripOut(ORMModel):
    id: int
    title: str
    description: str | None = None
    owner: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    item_count: int = 0
    items: list[TripItemOut] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TripSummary(ORMModel):
    id: int
    title: str
    owner: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    item_count: int = 0


# ---------------------------------------------------------------- Stats
class CountItem(BaseModel):
    key: str
    name: str
    count: int


class Overview(BaseModel):
    attractions: int
    free_attractions: int
    attractions_with_images: int
    cities: int
    towns: int
    categories: int
    images: int
    reviews: int
    trips: int
    by_service_status: list[CountItem]
    data_source: str
    data_update_time: str | None = None


class RatedAttraction(BaseModel):
    id: str
    name: str
    review_count: int
    average_rating: float
