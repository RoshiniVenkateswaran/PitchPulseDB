from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth
from sqlalchemy.orm import Session
from backend.core.config import settings
from backend.core.database import get_db
from backend.models.domain import User

# Initialize Firebase App
try:
    if settings.FIREBASE_KEY_PATH:
        cred = credentials.Certificate(settings.FIREBASE_KEY_PATH)
        firebase_admin.initialize_app(cred)
    else:
        # Fallback for demo if no key provided: use default app or stub
        firebase_admin.initialize_app()
except ValueError:
    pass # App already initialized

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        # Verify Firebase Token
        # NOTE: For hackathon local dev, if you send "test-token-admin" or "test-token-manager", we bypass verification
        if token == "test-token-admin":
            decoded_token = {"uid": "admin-123", "email": "admin@demo.com"}
        elif token == "test-token-manager":
            decoded_token = {"uid": "manager-123", "email": "manager@demo.com"}
        else:
            decoded_token = auth.verify_id_token(token)
            
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")

        # Get or create user in local DB
        user = db.query(User).filter(User.firebase_uid == uid).first()
        if not user:
            role = "admin" if "admin" in email else "manager"
            user = User(firebase_uid=uid, email=email, role=role)
            db.add(user)
            db.commit()
            db.refresh(user)

        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires administrator privileges"
        )
    return current_user
