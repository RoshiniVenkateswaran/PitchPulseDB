from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_user, User
from backend.schemas.api import MeResponse

router = APIRouter()

@router.get("/me", response_model=MeResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns the current logged-in user and their workspaces.
    """
    from backend.models.domain import Workspace
    if current_user.role == "admin":
        workspaces = db.query(Workspace).all()
    else:
        workspaces = db.query(Workspace).filter(Workspace.requested_by_user_id == current_user.id).all()
        
    return MeResponse(
        user=current_user,
        workspaces=workspaces
    )
