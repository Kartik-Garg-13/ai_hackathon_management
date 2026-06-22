from dataclasses import dataclass
from typing import Protocol

from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Reviewer, Team
from app.services.skill_taxonomy import project_required_categories

MIN_MATCH_SCORE = 10.0
ORG_CONFLICT_FUZZY_THRESHOLD = 82


@dataclass
class TeamProfile:
    team_id: int
    skills_text: str
    categories: set[str]
    domain_text: str


@dataclass
class ReviewerProfile:
    reviewer_id: int
    expertise_text: str
    organization: str | None


class Matcher(Protocol):
    def score(self, team: TeamProfile, reviewer: ReviewerProfile) -> float: ...


class TfidfMatcher:
    def score_all(self, team_profiles: list[TeamProfile], reviewer_profiles: list[ReviewerProfile]):
        corpus = [t.domain_text for t in team_profiles] + [r.expertise_text for r in reviewer_profiles]
        vectorizer = TfidfVectorizer(stop_words="english")
        vectors = vectorizer.fit_transform(corpus)
        n_teams = len(team_profiles)
        team_vectors = vectors[:n_teams]
        reviewer_vectors = vectors[n_teams:]
        return cosine_similarity(team_vectors, reviewer_vectors)


def build_team_profile(team: Team) -> TeamProfile:
    cats = {c.strip() for c in (team.skill_categories or "").split(",") if c.strip()}
    required = project_required_categories(team.project_idea or "")
    domain_text = f"{team.project_idea or ''} {' '.join(required)} {team.skill_categories or ''}"
    return TeamProfile(
        team_id=team.id,
        skills_text=team.skill_categories or "",
        categories=cats | required,
        domain_text=domain_text,
    )


def build_reviewer_profile(reviewer: Reviewer) -> ReviewerProfile:
    expertise_text = " ".join(reviewer.expertise) + f" {reviewer.industry or ''}"
    return ReviewerProfile(
        reviewer_id=reviewer.id,
        expertise_text=expertise_text,
        organization=reviewer.organization,
    )


def _build_assignment_explanation(score: float, matched_categories: list[str], reviewer_name: str) -> str:
    if not matched_categories:
        return f"No strong skill overlap found — {reviewer_name} assigned as the best available fallback."
    categories_text = ", ".join(matched_categories)
    if score >= 60:
        return f"Strong match — {reviewer_name} has direct expertise in {categories_text}, matching this project's needs closely."
    if score >= 30:
        return f"Good match — {reviewer_name}'s background in {categories_text} covers part of this project."
    return f"Partial match — {reviewer_name} has some relevant experience in {categories_text}, but it's a loose fit."


def has_conflict(team: Team, reviewer: Reviewer) -> str | None:
    if not reviewer.organization or not team.college:
        return None
    org = reviewer.organization.strip().lower()
    college = team.college.strip().lower()
    similarity = fuzz.token_sort_ratio(org, college)
    if similarity >= ORG_CONFLICT_FUZZY_THRESHOLD:
        return f"Same organization/college as team ({reviewer.organization})"
    return None


def assign_reviewers(
    teams: list[Team],
    reviewers: list[Reviewer],
    matcher: TfidfMatcher | None = None,
) -> list[dict]:
    if not teams or not reviewers:
        return []

    matcher = matcher or TfidfMatcher()
    team_profiles = [build_team_profile(t) for t in teams]
    reviewer_profiles = [build_reviewer_profile(r) for r in reviewers]
    sim_matrix = matcher.score_all(team_profiles, reviewer_profiles)

    load = {r.id: r.current_load for r in reviewers}
    max_load = {r.id: r.max_load for r in reviewers}

    results = []
    for ti, team in enumerate(teams):
        candidates = []
        for ri, reviewer in enumerate(reviewers):
            if load[reviewer.id] >= max_load[reviewer.id]:
                continue
            if has_conflict(team, reviewer):
                continue
            raw_score = float(sim_matrix[ti][ri]) * 100
            candidates.append((raw_score, reviewer, ri))

        if not candidates:
            results.append({
                "team_id": team.id,
                "reviewer_id": None,
                "match_score": 0.0,
                "explanation": "No eligible reviewer: all candidates conflicted or at full load.",
            })
            continue

        candidates.sort(key=lambda c: (-c[0], load[c[1].id]))
        best_score, best_reviewer, best_ri = candidates[0]
        final_score = max(best_score, MIN_MATCH_SCORE if best_score > 0 else 0.0)

        matched_categories = sorted(team_profiles[ti].categories & set(best_reviewer.expertise))
        explanation = _build_assignment_explanation(best_score, matched_categories, best_reviewer.name)
        load[best_reviewer.id] += 1

        results.append({
            "team_id": team.id,
            "reviewer_id": best_reviewer.id,
            "match_score": round(final_score, 2),
            "explanation": explanation,
        })

    return results
