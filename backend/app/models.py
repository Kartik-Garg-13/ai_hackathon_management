from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Organizer(Base):
    __tablename__ = "organizers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    password_salt: Mapped[str] = mapped_column(String(64))
    auth_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    organization_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    hackathons: Mapped[list["Hackathon"]] = relationship(back_populates="organizer")


class Hackathon(Base):
    __tablename__ = "hackathons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("organizers.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    documentation_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sponsors: Mapped[list] = mapped_column(JSON, default=list)
    themes: Mapped[list] = mapped_column(JSON, default=list)
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    allow_judges: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_mentors: Mapped[bool] = mapped_column(Boolean, default=True)
    registration_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    mode: Mapped[str | None] = mapped_column(String(16), nullable=True)
    venue: Mapped[str | None] = mapped_column(String(512), nullable=True)
    min_team_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_team_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eligibility_criteria: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    code_of_conduct: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    support_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    winners_revealed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | stopped | ended

    organizer: Mapped["Organizer"] = relationship(back_populates="hackathons")
    invite_links: Mapped[list["InviteLink"]] = relationship(back_populates="hackathon")


class InviteLink(Base):
    __tablename__ = "invite_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"))
    role: Mapped[str] = mapped_column(String(16))
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    hackathon: Mapped["Hackathon"] = relationship(back_populates="invite_links")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"))
    team_id_str: Mapped[str] = mapped_column(String(64), index=True)
    team_name: Mapped[str] = mapped_column(String(255))
    college: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_idea: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    skill_categories: Mapped[str | None] = mapped_column(String(512), nullable=True)
    team_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_health_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    project_novelty_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    github_repo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    demo_video_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    participants: Mapped[list["Participant"]] = relationship(back_populates="team")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="team")
    scores: Mapped[list["Score"]] = relationship(back_populates="team")


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"))
    registration_id: Mapped[str] = mapped_column(String(64), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    phone_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    college: Mapped[str | None] = mapped_column(String(255), nullable=True)
    skills: Mapped[str | None] = mapped_column(String(512), nullable=True)
    project_idea: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    team_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    claimed_ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approval_status: Mapped[str] = mapped_column(String(16), default="approved")
    github_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String(32), nullable=True)
    consent_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    dietary_restriction: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)

    final_trust_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fraud_ring_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    explanation: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    ground_truth_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    predicted_label: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    team: Mapped["Team | None"] = relationship(back_populates="participants")


class Reviewer(Base):
    __tablename__ = "reviewers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"))
    name: Mapped[str] = mapped_column(String(255))
    expertise: Mapped[list] = mapped_column(JSON, default=list)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    previous_reviews_count: Mapped[int] = mapped_column(Integer, default=0)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(16), default="judge")
    max_load: Mapped[int] = mapped_column(Integer, default=5)
    current_load: Mapped[int] = mapped_column(Integer, default=0)
    auth_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    availability_window: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    assignments: Mapped[list["Assignment"]] = relationship(back_populates="reviewer")
    scores: Mapped[list["Score"]] = relationship(back_populates="reviewer")


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("reviewers.id"))
    match_score: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(32), default="assigned")
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    team: Mapped["Team"] = relationship(back_populates="assignments")
    reviewer: Mapped["Reviewer"] = relationship(back_populates="assignments")


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"))
    assignment_id: Mapped[int | None] = mapped_column(ForeignKey("assignments.id"), nullable=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("reviewers.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    score: Mapped[float] = mapped_column(Float)
    criteria: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    comments: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    reviewer: Mapped["Reviewer"] = relationship(back_populates="scores")
    team: Mapped["Team"] = relationship(back_populates="scores")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    activity_type: Mapped[str] = mapped_column(String(64))
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PitchReview(Base):
    __tablename__ = "pitch_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    innovation_score: Mapped[float] = mapped_column(Float)
    technical_complexity: Mapped[str] = mapped_column(String(16))
    presentation_quality: Mapped[str] = mapped_column(String(16))
    issues: Mapped[list] = mapped_column(JSON, default=list)
    slide_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"))
    channel: Mapped[str] = mapped_column(String(32), default="group")
    sender_role: Mapped[str] = mapped_column(String(16))
    sender_id: Mapped[int] = mapped_column(Integer)
    sender_name: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(String(2048))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MentorQuery(Base):
    __tablename__ = "mentor_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    category: Mapped[str] = mapped_column(String(64))
    body: Mapped[str] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(16), default="open")
    assigned_mentor_id: Mapped[int | None] = mapped_column(ForeignKey("reviewers.id"), nullable=True)
    response: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
