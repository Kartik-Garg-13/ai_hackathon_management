from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    registration_id: str
    name: str
    email: str
    team_id: int | None = None
    college: str | None = None
    team_name: str | None = None
    project_idea: str | None = None
    final_trust_score: float | None = None
    final_risk_level: str | None = None
    confidence_score: float | None = None
    anomaly_score: float | None = None
    fraud_ring_id: int | None = None
    reasons: list | None = None
    explanation: str | None = None
    ground_truth_label: str | None = None
    predicted_label: str | None = None
    ip_address: str | None = None
    claimed_ip_address: str | None = None
    approval_status: str = "approved"
    github_username: str | None = None
    academic_year: str | None = None
    consent_accepted: bool = False
    dietary_restriction: str | None = None
    emergency_contact: str | None = None


class RegistrationAnalytics(BaseModel):
    total_registrations: int
    total_teams: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    average_trust_score: float
    fraud_rings_detected: int
    statistical_anomalies: int
    ground_truth_metrics: dict | None = None


class ReviewerCreate(BaseModel):
    name: str
    expertise: list[str]
    experience_years: int = 0
    previous_reviews_count: int = 0
    organization: str | None = None
    industry: str | None = None
    role: str = "judge"
    max_load: int = 5
    email: str | None = None
    linkedin_url: str | None = None
    availability_window: str | None = None
    bio: str | None = None


class ReviewerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    expertise: list[str]
    experience_years: int
    previous_reviews_count: int
    organization: str | None
    industry: str | None
    role: str
    max_load: int
    current_load: int
    email: str | None = None
    linkedin_url: str | None = None
    availability_window: str | None = None
    bio: str | None = None


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    reviewer_id: int
    match_score: float
    explanation: str
    status: str
    assigned_at: datetime


class ScoreCreate(BaseModel):
    reviewer_id: int
    team_id: int
    assignment_id: int | None = None
    score: float
    criteria: dict | None = None
    comments: str | None = None
    actor: str | None = None


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reviewer_id: int
    team_id: int
    score: float
    criteria: dict | None
    comments: str | None
    submitted_at: datetime


class BiasReportEntry(BaseModel):
    reviewer_id: int
    reviewer_name: str
    bias_risk_level: str
    confidence_label: str
    summary: str
    num_scores: int
    mean_score: float
    z_score: float
    bias_confidence: float
    flags: list[str]


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: int
    action: str
    actor: str | None
    before: dict | None
    after: dict | None
    reasoning: str | None
    timestamp: datetime


class PitchReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    innovation_score: float
    technical_complexity: str
    presentation_quality: str
    issues: list[str]
    slide_count: int
    created_at: datetime


class CopilotQuestion(BaseModel):
    question: str


class CopilotAnswer(BaseModel):
    answer: str
    matched_question: str | None
    confidence: float


class ActivityCreate(BaseModel):
    team_id: int
    activity_type: str
    note: str | None = None


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    activity_type: str
    note: str | None
    sender_name: str | None = None
    timestamp: datetime


class TeammateOut(BaseModel):
    id: int
    name: str
    email: str


class BurnoutReportEntry(BaseModel):
    team_id: int
    team_name: str
    burnout_risk_level: str
    summary: str
    hours_since_last_activity: float
    activity_count_recent: int


class NormalizedScoreEntry(BaseModel):
    score_id: int
    reviewer_id: int
    reviewer_name: str
    raw_score: float
    normalized_score: float
    explanation: str


class WinnerEntry(BaseModel):
    rank: int
    team_id: int
    team_name: str
    average_normalized_score: float
    num_scores: int


class WinnersResponse(BaseModel):
    revealed: bool
    revealed_at: datetime | None = None
    rankings: list[WinnerEntry] = []


class OrganizerSignup(BaseModel):
    name: str
    email: str
    password: str
    organization_name: str | None = None
    contact_phone: str | None = None
    logo_url: str | None = None


class OrganizerLogin(BaseModel):
    email: str
    password: str


class OrganizerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    organization_name: str | None = None
    contact_phone: str | None = None
    logo_url: str | None = None


class AuthSession(BaseModel):
    auth_token: str
    role: str
    name: str
    hackathon_id: int | None = None


class EmailLogin(BaseModel):
    email: str


class HackathonCreate(BaseModel):
    name: str
    description: str | None = None
    documentation_url: str | None = None
    sponsors: list[str] = []
    themes: list[str] = []
    start_date: datetime | None = None
    end_date: datetime | None = None
    allow_judges: bool = True
    allow_mentors: bool = True
    registration_deadline: datetime | None = None
    mode: str | None = None
    venue: str | None = None
    min_team_size: int | None = None
    max_team_size: int | None = None
    eligibility_criteria: str | None = None
    code_of_conduct: str | None = None
    support_email: str | None = None


class HackathonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organizer_id: int
    name: str
    description: str | None
    documentation_url: str | None
    sponsors: list[str]
    themes: list[str]
    start_date: datetime | None
    end_date: datetime | None
    allow_judges: bool
    allow_mentors: bool
    registration_deadline: datetime | None = None
    mode: str | None = None
    venue: str | None = None
    min_team_size: int | None = None
    max_team_size: int | None = None
    eligibility_criteria: str | None = None
    code_of_conduct: str | None = None
    support_email: str | None = None
    created_at: datetime
    status: str = "active"


class InviteLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hackathon_id: int
    role: str
    token: str


class InviteInfo(BaseModel):
    hackathon_id: int
    hackathon_name: str
    role: str


class ReviewerRegisterViaInvite(BaseModel):
    name: str
    email: str
    expertise: list[str]
    experience_years: int = 0
    organization: str | None = None
    industry: str | None = None
    linkedin_url: str | None = None
    availability_window: str | None = None
    bio: str | None = None
    max_load: int = 5


class ParticipantRegisterViaInvite(BaseModel):
    name: str
    email: str
    phone_number: str | None = None
    college: str | None = None
    skills: str | None = None
    project_idea: str | None = None
    team_name: str | None = None
    claimed_ip_address: str | None = None
    github_username: str | None = None
    academic_year: str | None = None
    consent_accepted: bool
    dietary_restriction: str | None = None
    emergency_contact: str | None = None


class ApprovalAction(BaseModel):
    participant_id: int
    approval_status: str


class ReanalyzeResult(BaseModel):
    participants_analyzed: int
    ground_truth_metrics: dict | None = None


class ChatMessageCreate(BaseModel):
    body: str


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_role: str
    sender_name: str
    body: str
    timestamp: datetime


class MentorQueryCreate(BaseModel):
    category: str
    body: str


class MentorQueryRespond(BaseModel):
    response: str


class MentorQueryRate(BaseModel):
    rating: int


class MentorQueryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    participant_id: int
    category: str
    body: str
    status: str
    assigned_mentor_id: int | None
    response: str | None
    rating: int | None
    created_at: datetime
    responded_at: datetime | None


class MentorLeaderboardEntry(BaseModel):
    mentor_id: int
    mentor_name: str
    response_count: int
    average_rating: float | None
    summary: str


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_name: str
    college: str | None = None
    project_idea: str | None = None
    skill_categories: str | None = None
    team_size: int | None = None
    github_repo_url: str | None = None
    demo_video_url: str | None = None


class TeamLinksUpdate(BaseModel):
    github_repo_url: str | None = None
    demo_video_url: str | None = None


class SimilarProjectPair(BaseModel):
    team_a_id: int
    team_a_name: str
    team_b_id: int
    team_b_name: str
    similarity: float


class ProjectCategoryOut(BaseModel):
    label: str
    team_count: int
    team_ids: list[int]


class SimilarityReport(BaseModel):
    duplicate_pairs: list[SimilarProjectPair]
    categories: list[ProjectCategoryOut]


class FileMatchOut(BaseModel):
    path_a: str
    path_b: str
    similarity: float
    method: str


class PlagiarismReport(BaseModel):
    team_a_id: int
    team_b_id: int
    overall_similarity: float
    risk_level: str
    file_matches: list[FileMatchOut]
    commit_stats: dict
    notes: list[str]


class TeamCategoryCount(BaseModel):
    category: str
    team_count: int


class TopTeamEntry(BaseModel):
    team_id: int
    team_name: str
    average_normalized_score: float


class JudgeDashboard(BaseModel):
    team_count: int
    active_team_count: int
    inactive_team_count: int
    category_distribution: list[TeamCategoryCount]
    top_teams: list[TopTeamEntry]
