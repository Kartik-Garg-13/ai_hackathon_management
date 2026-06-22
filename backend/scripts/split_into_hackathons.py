"""One-off data migration: copies (does not move) the existing teams and
participants from the main demo hackathon into 3 new "previous hackathon"
records under the same organizer, splitting along whole-team boundaries so
no team is ever divided across two hackathons. The original hackathon and
its data are left completely untouched.

Each new hackathon gets two synthetic judges and scores for every copied
team, then has its winners revealed immediately so it shows a real podium.

Run once: python scripts/split_into_hackathons.py
"""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.auth import generate_token
from app.database import SessionLocal
from app.models import Hackathon, Participant, Reviewer, Score, Team

SOURCE_HACKATHON_ID = 1

NEW_HACKATHONS = [
    {
        "name": "CodeStorm Winter 2025",
        "description": "A 36-hour winter hackathon focused on rapid prototyping across AI, web, and mobile tracks.",
        "days_ago_start": 200,
    },
    {
        "name": "InnovateX Spring 2025",
        "description": "A spring innovation sprint bringing together student builders for a weekend of shipping.",
        "days_ago_start": 130,
    },
    {
        "name": "ByteWars Autumn 2025",
        "description": "An autumn-season hackathon pitting teams against real-world problem statements.",
        "days_ago_start": 60,
    },
]

JUDGE_PANEL = [
    {"name": "Prof. Anika Rao", "expertise": ["AI/ML", "Data"], "experience_years": 8, "organization": "MUJ Faculty", "industry": "Academia", "availability_window": "Flexible", "bio": "Guest judge."},
    {"name": "Mr. Devraj Shah", "expertise": ["Frontend", "Backend", "Cloud/DevOps"], "experience_years": 6, "organization": "Industry Partner", "industry": "Software", "availability_window": "Flexible", "bio": "Guest judge."},
]


def chunk(items, n):
    size = (len(items) + n - 1) // n
    return [items[i : i + size] for i in range(0, len(items), size)]


def main():
    db = SessionLocal()
    source = db.get(Hackathon, SOURCE_HACKATHON_ID)
    if not source:
        print(f"Source hackathon {SOURCE_HACKATHON_ID} not found.")
        return

    source_teams = db.query(Team).filter(Team.hackathon_id == SOURCE_HACKATHON_ID).order_by(Team.id).all()
    print(f"Found {len(source_teams)} teams in source hackathon '{source.name}'.")

    groups = chunk(source_teams, len(NEW_HACKATHONS))
    now = datetime.utcnow()

    for spec, team_group in zip(NEW_HACKATHONS, groups):
        start = now - timedelta(days=spec["days_ago_start"])
        end = start + timedelta(days=2)
        new_hackathon = Hackathon(
            organizer_id=source.organizer_id,
            name=spec["name"],
            description=spec["description"],
            start_date=start,
            end_date=end,
            registration_deadline=start - timedelta(days=7),
            allow_judges=source.allow_judges,
            allow_mentors=source.allow_mentors,
            mode=source.mode,
        )
        db.add(new_hackathon)
        db.flush()
        print(f"Created hackathon '{new_hackathon.name}' (id={new_hackathon.id}) with {len(team_group)} teams.")

        judges = []
        for jspec in JUDGE_PANEL:
            judge = Reviewer(hackathon_id=new_hackathon.id, role="judge", auth_token=generate_token(), max_load=len(team_group), **jspec)
            db.add(judge)
            judges.append(judge)
        db.flush()

        for old_team in team_group:
            new_team = Team(
                hackathon_id=new_hackathon.id,
                team_id_str=f"{old_team.team_id_str}_copy{new_hackathon.id}",
                team_name=old_team.team_name,
                college=old_team.college,
                project_idea=old_team.project_idea,
                skill_categories=old_team.skill_categories,
                team_size=old_team.team_size,
                team_health_score=old_team.team_health_score,
                project_novelty_score=old_team.project_novelty_score,
                github_repo_url=old_team.github_repo_url,
                demo_video_url=old_team.demo_video_url,
            )
            db.add(new_team)
            db.flush()

            members = db.query(Participant).filter(Participant.team_id == old_team.id).all()
            for m in members:
                db.add(Participant(
                    hackathon_id=new_hackathon.id,
                    registration_id=generate_token()[:16],
                    team_id=new_team.id,
                    name=m.name,
                    email=m.email,
                    phone_number=m.phone_number,
                    college=m.college,
                    skills=m.skills,
                    project_idea=m.project_idea,
                    team_name=m.team_name,
                    final_trust_score=m.final_trust_score,
                    final_risk_level=m.final_risk_level,
                    confidence_score=m.confidence_score,
                    anomaly_score=m.anomaly_score,
                    fraud_ring_id=m.fraud_ring_id,
                    reasons=m.reasons,
                    explanation=m.explanation,
                    ground_truth_label=m.ground_truth_label,
                    predicted_label=m.predicted_label,
                    ip_address=m.ip_address,
                    github_username=m.github_username,
                    academic_year=m.academic_year,
                    consent_accepted=True,
                    approval_status="approved",
                ))

            for judge in judges:
                score_value = max(0.0, min(100.0, round(random.gauss(70, 12), 1)))
                db.add(Score(
                    hackathon_id=new_hackathon.id,
                    reviewer_id=judge.id,
                    team_id=new_team.id,
                    score=score_value,
                    criteria={"innovation": score_value, "technical": score_value},
                    comments="Auto-generated score for a previous hackathon",
                ))

        new_hackathon.winners_revealed_at = datetime.utcnow()
        db.commit()
        print(f"  -> copied {len(team_group)} teams, scored them, and revealed winners for '{new_hackathon.name}'.")

    print("Done.")


if __name__ == "__main__":
    main()
