from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_admin_user, User
from backend.models.domain import Workspace

router = APIRouter()

@router.get("/requests")
def get_requests(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    workspaces = db.query(Workspace).filter(Workspace.status == "pending").all()
    return {"requests": workspaces}

@router.post("/workspaces/{workspace_id}/approve")
def approve_workspace(workspace_id: str, current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
        
    ws.status = "approved"
    ws.approved_by_user_id = current_user.id
    db.commit()
    return {"status": "success", "workspace": ws}
