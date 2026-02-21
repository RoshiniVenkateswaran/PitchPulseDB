from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_user, User
from backend.models.domain import Fixture, PlayerMatchStat

router = APIRouter()

@router.get("/{fixture_id}/detail")
def get_fixture_detail(fixture_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    f = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not f:
         raise HTTPException(status_code=404, detail="Not found")
    stats = db.query(PlayerMatchStat).filter(PlayerMatchStat.fixture_id == fixture_id).all()
    return {"fixture": f, "player_stats": stats}
