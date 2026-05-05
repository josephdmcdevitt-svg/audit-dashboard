from __future__ import annotations

import os
import secrets
import string
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, String, Text, create_engine, select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


def _short_id() -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TeamMember(Base):
    __tablename__ = "team_members"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=_short_id)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[str] = mapped_column(String(40), nullable=False, default="Staff")
    hours_per_week: Mapped[int] = mapped_column(Integer, default=40)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Audit(Base):
    __tablename__ = "audits"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=_short_id)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phase: Mapped[str] = mapped_column(String(40), default="Pre-Planning")
    start_week: Mapped[str] = mapped_column(String(10), nullable=False)
    end_week: Mapped[str] = mapped_column(String(10), nullable=False)
    budgeted_hours: Mapped[int] = mapped_column(Integer, default=0)
    type: Mapped[str] = mapped_column(String(40), default="Control Testing")
    risk_rating: Mapped[str] = mapped_column(String(20), default="Medium")
    likelihood: Mapped[int] = mapped_column(Integer, default=3)
    impact: Mapped[int] = mapped_column(Integer, default=3)
    completion_pct: Mapped[int] = mapped_column(Integer, default=0)
    owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sponsor: Mapped[str | None] = mapped_column(String(120), nullable=True)
    objectives: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    workpaper_url: Mapped[str | None] = mapped_column(String(400), nullable=True)
    business_unit: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan", lazy="selectin"
    )
    notes: Mapped[list["Note"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan", lazy="selectin"
    )


class Assignment(Base):
    __tablename__ = "assignments"
    audit_id: Mapped[str] = mapped_column(ForeignKey("audits.id", ondelete="CASCADE"), primary_key=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("team_members.id", ondelete="CASCADE"), primary_key=True)
    hours_per_week: Mapped[int] = mapped_column(Integer, default=0)
    audit: Mapped[Audit] = relationship(back_populates="assignments")


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=_short_id)
    audit_id: Mapped[str] = mapped_column(ForeignKey("audits.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(120), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    audit: Mapped[Audit] = relationship(back_populates="notes")


class ActivityEntry(Base):
    __tablename__ = "activity_log"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=_short_id)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    user: Mapped[str] = mapped_column(String(120), default="system")


_engine = None


def _ensure_dir(url: str) -> None:
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
        Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_engine():
    global _engine
    if _engine is None:
        url = os.environ.get("DATABASE_URL", "sqlite:///data/workspace.db")
        _ensure_dir(url)
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args, future=True)
        Base.metadata.create_all(_engine)
    return _engine


@contextmanager
def session_scope():
    sess = Session(get_engine(), expire_on_commit=False)
    try:
        yield sess
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    finally:
        sess.close()


def list_members() -> list[TeamMember]:
    with session_scope() as s:
        return list(s.scalars(select(TeamMember).order_by(TeamMember.name)))


def list_audits() -> list[Audit]:
    with session_scope() as s:
        return list(s.scalars(select(Audit).order_by(Audit.start_week)))


def list_activity(limit: int = 500) -> list[ActivityEntry]:
    with session_scope() as s:
        return list(s.scalars(select(ActivityEntry).order_by(ActivityEntry.timestamp.desc()).limit(limit)))


def get_audit(audit_id: str) -> Audit | None:
    with session_scope() as s:
        return s.get(Audit, audit_id)


def log_activity(action: str, detail: str = "", user: str = "system") -> None:
    with session_scope() as s:
        s.add(ActivityEntry(action=action, detail=detail, user=user))


def upsert_member(member_id: str | None, **fields) -> str:
    with session_scope() as s:
        if member_id:
            m = s.get(TeamMember, member_id)
            if m is None:
                raise ValueError(f"Unknown member {member_id}")
            for k, v in fields.items():
                setattr(m, k, v)
            return m.id
        m = TeamMember(**fields)
        s.add(m)
        s.flush()
        return m.id


def delete_member(member_id: str) -> None:
    with session_scope() as s:
        m = s.get(TeamMember, member_id)
        if m:
            s.delete(m)


def upsert_audit(audit_id: str | None, **fields) -> str:
    with session_scope() as s:
        if audit_id:
            a = s.get(Audit, audit_id)
            if a is None:
                raise ValueError(f"Unknown audit {audit_id}")
            for k, v in fields.items():
                setattr(a, k, v)
            return a.id
        a = Audit(**fields)
        s.add(a)
        s.flush()
        return a.id


def delete_audit(audit_id: str) -> None:
    with session_scope() as s:
        a = s.get(Audit, audit_id)
        if a:
            s.delete(a)


def replace_assignments(audit_id: str, assignments: list[tuple[str, int]]) -> None:
    with session_scope() as s:
        a = s.get(Audit, audit_id)
        if a is None:
            return
        a.assignments.clear()
        s.flush()
        for mid, hrs in assignments:
            if hrs > 0:
                s.add(Assignment(audit_id=audit_id, member_id=mid, hours_per_week=hrs))


def update_completion(audit_id: str, pct: int) -> None:
    with session_scope() as s:
        a = s.get(Audit, audit_id)
        if a:
            a.completion_pct = max(0, min(100, pct))


def add_note(audit_id: str, text: str, author: str) -> None:
    with session_scope() as s:
        s.add(Note(audit_id=audit_id, text=text, author=author))


def delete_note(note_id: str) -> None:
    with session_scope() as s:
        n = s.get(Note, note_id)
        if n:
            s.delete(n)
