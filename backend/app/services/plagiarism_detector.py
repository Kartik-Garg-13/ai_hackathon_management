import ast
import difflib
from dataclasses import dataclass, field

import httpx

from app.services.repo_inspector import fetch_repo_tree, parse_github_url

CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb",
    ".c", ".cpp", ".cs", ".php", ".rs", ".kt", ".swift",
}
MAX_FILES_PER_REPO = 25
MAX_FILE_BYTES = 60_000
HIGH_RISK_THRESHOLD = 0.7


@dataclass
class FileMatch:
    path_a: str
    path_b: str
    similarity: float
    method: str  # "ast" | "text"


@dataclass
class RepoComparison:
    overall_similarity: float
    risk_level: str
    file_matches: list[FileMatch] = field(default_factory=list)
    commit_stats: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _pick_files(paths: list[str]) -> list[str]:
    code_paths = [p for p in paths if any(p.lower().endswith(ext) for ext in CODE_EXTENSIONS)]
    return code_paths[:MAX_FILES_PER_REPO]


def fetch_file_contents(owner: str, repo: str, paths: list[str], client: httpx.Client, branch: str = "main") -> dict[str, str]:
    repo_resp = client.get(f"https://api.github.com/repos/{owner}/{repo}")
    if repo_resp.status_code == 200:
        branch = repo_resp.json().get("default_branch", branch)

    contents = {}
    for path in paths:
        try:
            resp = client.get(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}")
            if resp.status_code == 200 and len(resp.content) <= MAX_FILE_BYTES:
                contents[path] = resp.text
        except httpx.HTTPError:
            continue
    return contents


def fetch_commit_stats(owner: str, repo: str, client: httpx.Client) -> dict:
    resp = client.get(f"https://api.github.com/repos/{owner}/{repo}/commits", params={"per_page": 100})
    if resp.status_code != 200:
        return {"commit_count": None, "first_commit_at": None, "last_commit_at": None}
    commits = resp.json()
    if not commits:
        return {"commit_count": 0, "first_commit_at": None, "last_commit_at": None}
    dates = [c["commit"]["author"]["date"] for c in commits if c.get("commit")]
    return {
        "commit_count": len(commits) if len(commits) < 100 else "100+",
        "first_commit_at": min(dates) if dates else None,
        "last_commit_at": max(dates) if dates else None,
    }


def _ast_similarity(text_a: str, text_b: str) -> float | None:
    try:
        dump_a = ast.dump(ast.parse(text_a))
        dump_b = ast.dump(ast.parse(text_b))
    except SyntaxError:
        return None
    return difflib.SequenceMatcher(None, dump_a, dump_b).ratio()


def _text_similarity(text_a: str, text_b: str) -> float:
    return difflib.SequenceMatcher(None, text_a, text_b).ratio()


def compare_file_sets(files_a: dict[str, str], files_b: dict[str, str]) -> list[FileMatch]:
    matches = []
    for path_a, text_a in files_a.items():
        for path_b, text_b in files_b.items():
            is_python = path_a.endswith(".py") and path_b.endswith(".py")
            if is_python:
                score = _ast_similarity(text_a, text_b)
                if score is not None:
                    matches.append(FileMatch(path_a=path_a, path_b=path_b, similarity=round(score, 3), method="ast"))
                    continue
            score = _text_similarity(text_a, text_b)
            matches.append(FileMatch(path_a=path_a, path_b=path_b, similarity=round(score, 3), method="text"))
    matches.sort(key=lambda m: m.similarity, reverse=True)
    return matches


@dataclass
class RepoSnapshot:
    github_url: str
    files: dict[str, str] = field(default_factory=dict)
    commit_stats: dict = field(default_factory=dict)
    error: str | None = None


def fetch_repo_snapshot(github_url: str, client: httpx.Client | None = None) -> RepoSnapshot:
    parsed = parse_github_url(github_url)
    if not parsed:
        return RepoSnapshot(github_url=github_url, error="GitHub URL could not be parsed")

    own_client = client is None
    client = client or httpx.Client(timeout=10.0)
    try:
        try:
            paths = _pick_files(fetch_repo_tree(*parsed, client=client))
        except Exception as exc:
            return RepoSnapshot(github_url=github_url, error=f"Could not fetch repository: {exc}")
        files = fetch_file_contents(*parsed, paths, client)
        commit_stats = fetch_commit_stats(*parsed, client)
        return RepoSnapshot(github_url=github_url, files=files, commit_stats=commit_stats)
    finally:
        if own_client:
            client.close()


def compare_snapshots(snapshot_a: RepoSnapshot, snapshot_b: RepoSnapshot) -> RepoComparison:
    notes = []
    if snapshot_a.error or snapshot_b.error:
        notes = [n for n in (snapshot_a.error, snapshot_b.error) if n]
        return RepoComparison(overall_similarity=0.0, risk_level="unknown", notes=notes)
    if not snapshot_a.files or not snapshot_b.files:
        notes.append("Could not retrieve enough source files for a meaningful comparison")
        return RepoComparison(
            overall_similarity=0.0, risk_level="unknown", notes=notes,
            commit_stats={"a": snapshot_a.commit_stats, "b": snapshot_b.commit_stats},
        )

    matches = compare_file_sets(snapshot_a.files, snapshot_b.files)
    top_matches = matches[:5]
    overall = round(sum(m.similarity for m in top_matches) / len(top_matches), 3) if top_matches else 0.0

    risk_level = "high" if overall >= HIGH_RISK_THRESHOLD else "medium" if overall >= 0.45 else "low"
    if len(snapshot_a.files) < 3 or len(snapshot_b.files) < 3:
        notes.append("Small sample of files compared — confidence is limited")

    return RepoComparison(
        overall_similarity=overall,
        risk_level=risk_level,
        file_matches=matches[:15],
        commit_stats={"a": snapshot_a.commit_stats, "b": snapshot_b.commit_stats},
        notes=notes,
    )


def compare_repos(github_url_a: str, github_url_b: str) -> RepoComparison:
    with httpx.Client(timeout=10.0) as client:
        snapshot_a = fetch_repo_snapshot(github_url_a, client=client)
        snapshot_b = fetch_repo_snapshot(github_url_b, client=client)
    return compare_snapshots(snapshot_a, snapshot_b)
