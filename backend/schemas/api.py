from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

# Common Models
class WorkspaceBase(BaseModel):
    id: str
    provider_team_id: int
    team_name: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class PlayerBase(BaseModel):
    id: str
    name: str
    position: Optional[str]
    jersey: Optional[int]
    class Config:
        from_attributes = True

class FixtureBase(BaseModel):
    id: str
    provider_fixture_id: int
    kickoff: datetime
    opponent_name: str
    home_away: str
    status: str
    score_home: Optional[int]
    score_away: Optional[int]
    class Config:
        from_attributes = True

# Responses
class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    class Config:
        from_attributes = True

class MeResponse(BaseModel):
    user: UserResponse
    workspaces: List[WorkspaceBase]

class TeamSearchItem(BaseModel):
    provider_team_id: int
    name: str
    logo_url: Optional[str] = None

class TeamSearchResponse(BaseModel):
    teams: List[TeamSearchItem]

class RequestAccessRequest(BaseModel):
    provider_team_id: int

class RequestAccessResponse(WorkspaceBase):
    pass

class PlayerTile(BaseModel):
    player: PlayerBase
    readiness_score: float
    risk_score: float
    risk_band: str
    top_drivers: List[str]

class WorkspaceHomeResponse(BaseModel):
    workspace: WorkspaceBase
    next_fixture: Optional[FixtureBase]
    recent_fixtures: List[FixtureBase]
    squad: List[PlayerTile]

class PlayerStatus(BaseModel):
    readiness_score: float
    risk_score: float
    risk_band: str
    acute_load: float
    chronic_load: float
    acwr: float

class WeeklyHistoryRecord(BaseModel):
    week_start: datetime
    risk_score: float
    readiness_score: float
    acute_load: float
    acwr: float

class PlayerDetailResponse(BaseModel):
    player: PlayerBase
    current_status: PlayerStatus
    weekly_history: List[WeeklyHistoryRecord]

class Driver(BaseModel):
    factor: str
    value: str
    threshold: str
    impact: str

class PlayerWhyResponse(BaseModel):
    drivers: List[Driver]

class SimilarCase(BaseModel):
    player_name: str
    week_date: datetime
    similarity_score: float
    context: str
    action_taken: str

class SimilarCasesResponse(BaseModel):
    cases: List[SimilarCase]

class ActionPlanResponse(BaseModel):
    summary: str
    why: List[str]
    recommendations: List[str]
    caution: str

class MatchReportResponse(BaseModel):
    match_summary: str
    squad_load_assessment: str
    critical_flags: List[str]

class MovementAnalysisResponse(BaseModel):
    mechanical_risk_band: str
    flags: List[str]
    coaching_cues: List[str]
    confidence: float

class SyncResponse(BaseModel):
    status: str
    players_synced: Optional[int] = 0
    fixtures_synced: Optional[int] = 0
    fixtures_processed: Optional[int] = 0
    stats_ingested: Optional[int] = 0
