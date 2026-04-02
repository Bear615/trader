from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_admin
from app.models.ai_decision import AIDecision

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(require_admin)])


@router.get("/decisions")
def list_decisions(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(AIDecision).order_by(AIDecision.timestamp.desc())
    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [d.to_dict(include_raw=True) for d in items],
    }


@router.get("/decisions/{decision_id}")
def get_decision(decision_id: int, db: Session = Depends(get_db)):
    decision = db.get(AIDecision, decision_id)
    if not decision:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision.to_dict(include_raw=True)
