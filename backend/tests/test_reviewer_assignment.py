from app.models import Reviewer, Team
from app.services.reviewer_assignment import assign_reviewers, build_team_profile, has_conflict


def make_team(id_, college, skills, project_idea):
    return Team(id=id_, team_id_str=f"T{id_}", team_name=f"Team{id_}", college=college,
                project_idea=project_idea, skill_categories=skills, team_size=2)


def make_reviewer(id_, name, expertise, organization, max_load=5):
    return Reviewer(id=id_, name=name, expertise=expertise, organization=organization,
                     experience_years=5, max_load=max_load, current_load=0)


def test_conflict_detection_blocks_same_organization():
    team = make_team(1, "IIT Delhi", "AI/ML", "AI Chatbot")
    reviewer = make_reviewer(1, "Dr. X", ["AI/ML"], "IIT Delhi")
    assert has_conflict(team, reviewer) is not None


def test_no_conflict_for_different_organization():
    team = make_team(1, "IIT Delhi", "AI/ML", "AI Chatbot")
    reviewer = make_reviewer(1, "Dr. X", ["AI/ML"], "NIT Trichy")
    assert has_conflict(team, reviewer) is None


def test_conflict_detection_catches_spelling_variant_of_same_org():
    team = make_team(1, "Lagos Polytechnic Institute", "AI/ML", "AI Chatbot")
    reviewer = make_reviewer(1, "Dr. X", ["AI/ML"], "Lagos Polytechnic Inst.")
    assert has_conflict(team, reviewer) is not None


def test_no_conflict_for_orgs_sharing_a_common_prefix():
    team = make_team(1, "VIT Vellore", "AI/ML", "AI Chatbot")
    reviewer = make_reviewer(1, "Dr. X", ["AI/ML"], "VIT Chennai")
    assert has_conflict(team, reviewer) is None


def test_assignment_prefers_matching_expertise():
    ai_team = make_team(1, "IIT Bombay", "AI/ML, Data", "Deepfake Detection Platform")
    web_team = make_team(2, "NIT Trichy", "Frontend, Backend", "Web Portal for Farmers")
    ai_reviewer = make_reviewer(1, "AI Reviewer", ["AI/ML", "Data"], "Org A")
    web_reviewer = make_reviewer(2, "Web Reviewer", ["Frontend", "Backend"], "Org B")

    results = assign_reviewers([ai_team, web_team], [ai_reviewer, web_reviewer])
    by_team = {r["team_id"]: r for r in results}
    assert by_team[1]["reviewer_id"] == 1
    assert by_team[2]["reviewer_id"] == 2


def test_assignment_respects_load_capacity():
    teams = [make_team(i, "College", "AI/ML", "AI project") for i in range(1, 4)]
    reviewer = make_reviewer(1, "Sole Reviewer", ["AI/ML"], "Org", max_load=2)

    results = assign_reviewers(teams, [reviewer])
    assigned = [r for r in results if r["reviewer_id"] is not None]
    unassigned = [r for r in results if r["reviewer_id"] is None]
    assert len(assigned) == 2
    assert len(unassigned) == 1


def test_conflicted_reviewer_excluded_even_if_best_match():
    team = make_team(1, "IIT Delhi", "AI/ML", "AI project")
    conflicted = make_reviewer(1, "Conflicted", ["AI/ML"], "IIT Delhi")
    fallback = make_reviewer(2, "Fallback", ["Frontend"], "Org B")

    results = assign_reviewers([team], [conflicted, fallback])
    assert results[0]["reviewer_id"] == 2


def test_team_profile_categories_are_read_directly_not_recategorized():
    team = make_team(1, "IIT Delhi", "Cloud/DevOps, Data, Other", "Smart Irrigation System")
    profile = build_team_profile(team)
    assert profile.categories >= {"Cloud/DevOps", "Data", "Other"}
