from app.services.similarity_detector import TeamProject, categorize_projects, find_similar_projects


def test_finds_near_duplicate_project_descriptions():
    projects = [
        TeamProject(team_id=1, team_name="Alpha", text="AI Resume Screener for recruiters"),
        TeamProject(team_id=2, team_name="Beta", text="AI Resume Analyzer for recruiters"),
        TeamProject(team_id=3, team_name="Gamma", text="Blockchain based land registry system"),
    ]
    pairs = find_similar_projects(projects, threshold=0.4)
    assert len(pairs) == 1
    assert {pairs[0].team_a_id, pairs[0].team_b_id} == {1, 2}
    assert pairs[0].similarity > 0.4


def test_no_duplicates_when_projects_are_distinct():
    projects = [
        TeamProject(team_id=1, team_name="Alpha", text="Mental health companion mobile app"),
        TeamProject(team_id=2, team_name="Beta", text="Smart irrigation system for farmers"),
    ]
    assert find_similar_projects(projects) == []


def test_categorize_projects_groups_similar_ideas():
    projects = [
        TeamProject(team_id=1, team_name="A1", text="AI resume screener tool for recruiters"),
        TeamProject(team_id=2, team_name="A2", text="AI resume ranking tool for recruiters"),
        TeamProject(team_id=3, team_name="A3", text="AI resume parser for recruiters"),
        TeamProject(team_id=4, team_name="B1", text="Hospital patient queue management system"),
        TeamProject(team_id=5, team_name="B2", text="Hospital appointment scheduling system"),
        TeamProject(team_id=6, team_name="B3", text="Hospital bed availability tracker"),
    ]
    categories = categorize_projects(projects, max_clusters=2)
    assert len(categories) >= 1
    assert sum(c.team_count for c in categories) == 6


def test_handles_empty_and_blank_input():
    assert find_similar_projects([]) == []
    assert categorize_projects([]) == []
    assert categorize_projects([TeamProject(team_id=1, team_name="A", text="")]) == []
