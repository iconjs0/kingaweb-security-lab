"""Tables: users/teams/labs/sessions/submissions/competitions/audit. Audit is append-only by convention (no update/delete paths)."""
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), default="learner")  # learner|instructor|content-author|platform-admin
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    owner_id: Mapped[str] = mapped_column(String(64))

class Membership(Base):
    __tablename__ = "memberships"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)

class Lab(Base):
    __tablename__ = "labs"
    slug: Mapped[str] = mapped_column(String(128), primary_key=True)
    version: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text, default="")
    track: Mapped[str] = mapped_column(String(64), default="web")
    difficulty: Mapped[str] = mapped_column(String(32), default="beginner")
    time_minutes: Mapped[int] = mapped_column(Integer, default=60)
    ttl_minutes: Mapped[int] = mapped_column(Integer, default=60)
    objectives_json: Mapped[str] = mapped_column(Text, default="[]")
    targets_json: Mapped[str] = mapped_column(Text, default="[]")

class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    lab_slug: Mapped[str] = mapped_column(String(128))
    lab_version: Mapped[str] = mapped_column(String(32))
    seed_hex: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="active")
    competition_id: Mapped[str] = mapped_column(String(64), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=True)
    targets_json: Mapped[str] = mapped_column(Text, default="[]")  # orchestrator connection details
    expires_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    objective_id: Mapped[str] = mapped_column(String(128))
    flag_hash: Mapped[str] = mapped_column(String(64))
    correct: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Competition(Base):
    __tablename__ = "competitions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    owner_id: Mapped[str] = mapped_column(String(64))
    frozen: Mapped[int] = mapped_column(Integer, default=0)

class Enrollment(Base):
    __tablename__ = "enrollments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    competition_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)

class Audit(Base):
    __tablename__ = "audit"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(128))
    target: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
