"""遊客評論 (reviews)：可從 /reviews 或巢狀的 /attractions/{id}/reviews 存取。"""
from enum import Enum

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.common import (
    PageParams,
    get_or_404,
    make_page,
    page_params,
    paginate,
    reject_nulls,
    review_out,
    unprocessable,
)
from app.database import get_db
from app.security import require_api_key

router = APIRouter(prefix="/reviews", tags=["Reviews 評論"])
nested = APIRouter(prefix="/attractions/{attraction_id}/reviews", tags=["Reviews 評論"])


class ReviewSort(str, Enum):
    newest = "-created_at"
    oldest = "created_at"
    rating_desc = "-rating"
    rating = "rating"


SORTS = {
    ReviewSort.newest: models.Review.created_at.desc(),
    ReviewSort.oldest: models.Review.created_at,
    ReviewSort.rating_desc: models.Review.rating.desc(),
    ReviewSort.rating: models.Review.rating,
}


def _query(attraction_id=None, author=None, min_rating=None, max_rating=None, sort=ReviewSort.newest):
    R = models.Review
    stmt = select(R).options(joinedload(R.attraction))
    if attraction_id:
        stmt = stmt.where(R.attraction_id == attraction_id)
    if author:
        stmt = stmt.where(R.author == author)
    if min_rating:
        stmt = stmt.where(R.rating >= min_rating)
    if max_rating:
        stmt = stmt.where(R.rating <= max_rating)
    return stmt.order_by(SORTS[sort], R.id.desc())


def _create(db: Session, attraction_id: str, fields: schemas.ReviewFields, response: Response):
    r = models.Review(attraction_id=attraction_id, **fields.model_dump(exclude={"attraction_id"}))
    db.add(r)
    db.commit()
    db.refresh(r)
    response.headers["Location"] = f"/api/v1/reviews/{r.id}"
    return review_out(r)


@router.get("", response_model=schemas.Page[schemas.ReviewOut], summary="查詢評論列表")
def list_reviews(
    response: Response,
    attraction_id: str | None = Query(None, description="景點 ID"),
    author: str | None = Query(None, description="作者"),
    min_rating: int | None = Query(None, ge=1, le=5, description="最低評分"),
    max_rating: int | None = Query(None, ge=1, le=5, description="最高評分"),
    sort: ReviewSort = Query(ReviewSort.newest, description="排序方式"),
    params: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    stmt = _query(attraction_id, author, min_rating, max_rating, sort)
    total, rows = paginate(db, stmt, params, response)
    return make_page(total, params, [review_out(r) for r in rows])


@router.get("/{review_id}", response_model=schemas.ReviewOut, summary="取得單一評論")
def get_review(review_id: int, db: Session = Depends(get_db)):
    return review_out(get_or_404(db, models.Review, review_id, "Review"))


@router.post(
    "",
    response_model=schemas.ReviewOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="新增評論",
)
def create_review(body: schemas.ReviewCreate, response: Response, db: Session = Depends(get_db)):
    if not db.get(models.Attraction, body.attraction_id):
        raise unprocessable(f"Attraction '{body.attraction_id}' 不存在")
    return _create(db, body.attraction_id, body, response)


def _update(db: Session, review_id: int, data: dict) -> schemas.ReviewOut:
    r = get_or_404(db, models.Review, review_id, "Review")
    for k, v in data.items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return review_out(r)


@router.put("/{review_id}", response_model=schemas.ReviewOut, dependencies=[Depends(require_api_key)], summary="整筆更新評論")
def replace_review(review_id: int, body: schemas.ReviewFields, db: Session = Depends(get_db)):
    return _update(db, review_id, body.model_dump())


@router.patch("/{review_id}", response_model=schemas.ReviewOut, dependencies=[Depends(require_api_key)], summary="部分更新評論")
def update_review(review_id: int, body: schemas.ReviewUpdate, db: Session = Depends(get_db)):
    return _update(db, review_id, reject_nulls(body.model_dump(exclude_unset=True), "author", "rating"))


@router.delete(
    "/{review_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_api_key)], summary="刪除評論"
)
def delete_review(review_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, models.Review, review_id, "Review"))
    db.commit()


# ---------------------------------------------------------------- nested
@nested.get("", response_model=schemas.Page[schemas.ReviewOut], summary="列出某景點的評論")
def list_attraction_reviews(
    attraction_id: str,
    response: Response,
    sort: ReviewSort = Query(ReviewSort.newest),
    params: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    get_or_404(db, models.Attraction, attraction_id, "Attraction")
    total, rows = paginate(db, _query(attraction_id, sort=sort), params, response)
    return make_page(total, params, [review_out(r) for r in rows])


@nested.post(
    "",
    response_model=schemas.ReviewOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="為某景點新增評論",
)
def create_attraction_review(
    attraction_id: str, body: schemas.ReviewFields, response: Response, db: Session = Depends(get_db)
):
    get_or_404(db, models.Attraction, attraction_id, "Attraction")
    return _create(db, attraction_id, body, response)
