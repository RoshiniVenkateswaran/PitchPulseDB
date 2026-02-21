from fastapi import APIRouter

api_router = APIRouter()

from backend.api import auth, workspaces, players, sync, admin, fixtures
api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["Workspaces"])
api_router.include_router(players.router, prefix="/players", tags=["Players"])
api_router.include_router(fixtures.router, prefix="/fixtures", tags=["Fixtures"])
api_router.include_router(sync.router, prefix="/sync", tags=["Sync"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
