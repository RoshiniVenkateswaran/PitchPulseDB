from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from backend.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="manager") # admin or manager
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(String, primary_key=True, default=generate_uuid)
    provider_team_id = Column(Integer, index=True, nullable=False)
    team_name = Column(String, nullable=False)
    status = Column(String, default="pending") # pending, approved
    requested_by_user_id = Column(String, ForeignKey("users.id"))
    approved_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Player(Base):
    __tablename__ = "players"
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    provider_player_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    position = Column(String)
    jersey = Column(Integer)
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Fixture(Base):
    __tablename__ = "fixtures"
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    provider_fixture_id = Column(Integer, index=True, nullable=False)
    kickoff = Column(DateTime(timezone=True), nullable=False)
    opponent_name = Column(String, nullable=False)
    home_away = Column(String, nullable=False)
    status = Column(String, nullable=False) # e.g., 'NS', 'FT'
    score_home = Column(Integer, nullable=True)
    score_away = Column(Integer, nullable=True)
    last_synced_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PlayerMatchStat(Base):
    __tablename__ = "player_match_stats"
    id = Column(String, primary_key=True, default=generate_uuid)
    fixture_id = Column(String, ForeignKey("fixtures.id"), nullable=False, index=True)
    player_id = Column(String, ForeignKey("players.id"), nullable=False, index=True)
    minutes = Column(Integer, default=0)
    stats_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DailyLoad(Base):
    __tablename__ = "daily_load"
    id = Column(String, primary_key=True, default=generate_uuid)
    player_id = Column(String, ForeignKey("players.id"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False)
    source = Column(String, nullable=False) # match, training, checkin
    load_value = Column(Float, nullable=False)
    meta_json = Column(JSON, default={})

class WeeklyMetric(Base):
    __tablename__ = "weekly_metrics"
    id = Column(String, primary_key=True, default=generate_uuid)
    player_id = Column(String, ForeignKey("players.id"), nullable=False, index=True)
    week_start = Column(DateTime(timezone=True), nullable=False)
    acute_load = Column(Float, default=0.0)
    chronic_load = Column(Float, default=0.0)
    acwr = Column(Float, default=0.0)
    monotony = Column(Float, default=0.0)
    strain = Column(Float, default=0.0)
    readiness_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    risk_band = Column(String, default="LOW")
    drivers_json = Column(JSON, default=[])

class MatchReport(Base):
    __tablename__ = "match_reports"
    id = Column(String, primary_key=True, default=generate_uuid)
    fixture_id = Column(String, ForeignKey("fixtures.id"), nullable=False, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    report_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
