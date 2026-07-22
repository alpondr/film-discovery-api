from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.models.search_log import SearchLog
from app.models.user import User
from app.schemas.search_log import PaginatedSearchLogs, SearchLogOut

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=PaginatedSearchLogs)
def get_search_history(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # only ever the current user's own logs - never let one user page through another's history
    base_query = db.query(SearchLog).filter(SearchLog.user_id == current_user.id)
    total = base_query.count()

    items = (
        base_query.order_by(SearchLog.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    pages = (total + size - 1) // size if total > 0 else 0

    return PaginatedSearchLogs(
        items=[SearchLogOut.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )
