from app.services.plagiarism_detector import RepoSnapshot, compare_file_sets, compare_snapshots
from app.services.repo_inspector import parse_github_url


def test_parse_github_url_variants():
    assert parse_github_url("https://github.com/octocat/hello-world") == ("octocat", "hello-world")
    assert parse_github_url("https://github.com/octocat/hello-world.git") == ("octocat", "hello-world")
    assert parse_github_url("github.com/octocat/hello-world/") == ("octocat", "hello-world")
    assert parse_github_url("not a url") is None
    assert parse_github_url("") is None


def test_compare_file_sets_uses_ast_for_python_and_flags_identical_logic():
    code_a = "def add(a, b):\n    return a + b\n"
    code_b = "def add(x, y):\n    return x + y\n"
    matches = compare_file_sets({"a.py": code_a}, {"b.py": code_b})
    assert len(matches) == 1
    assert matches[0].method == "ast"
    assert matches[0].similarity > 0.9


def test_compare_file_sets_falls_back_to_text_for_non_python():
    matches = compare_file_sets({"a.js": "function add(a,b){return a+b;}"}, {"b.js": "function add(a,b){return a+b;}"})
    assert matches[0].method == "text"
    assert matches[0].similarity == 1.0


def test_compare_snapshots_flags_high_similarity_repos():
    snap_a = RepoSnapshot(github_url="a", files={"main.py": "def f():\n    return 1\n"})
    snap_b = RepoSnapshot(github_url="b", files={"main.py": "def f():\n    return 1\n"})
    result = compare_snapshots(snap_a, snap_b)
    assert result.risk_level == "high"
    assert result.overall_similarity == 1.0


def test_compare_snapshots_reports_error_notes():
    snap_a = RepoSnapshot(github_url="a", error="GitHub URL could not be parsed")
    snap_b = RepoSnapshot(github_url="b", files={"x.py": "x = 1"})
    result = compare_snapshots(snap_a, snap_b)
    assert result.risk_level == "unknown"
    assert "GitHub URL could not be parsed" in result.notes
