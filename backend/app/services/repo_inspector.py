import re

import httpx

TEST_PATH_HINTS = ("test", "tests", "spec", "__tests__", "specs")
CI_PATH_HINTS = (".github/workflows", ".gitlab-ci.yml", ".circleci", "azure-pipelines.yml")
DEPLOY_FILE_HINTS = (
    "dockerfile", "docker-compose.yml", "procfile", "vercel.json", "netlify.toml",
    "render.yaml", "fly.toml", "app.yaml", "k8s", "kubernetes",
)
README_HINTS = ("readme.md", "readme.rst", "readme.txt", "readme")

GITHUB_URL_RE = re.compile(r"github\.com[:/]+([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")


def parse_github_url(url: str) -> tuple[str, str] | None:
    if not url:
        return None
    match = GITHUB_URL_RE.search(url.strip())
    if not match:
        return None
    return match.group(1), match.group(2)


def fetch_repo_tree(owner: str, repo: str, client: httpx.Client | None = None) -> list[str]:
    own_client = client is None
    client = client or httpx.Client(timeout=10.0)
    try:
        repo_resp = client.get(f"https://api.github.com/repos/{owner}/{repo}")
        if repo_resp.status_code != 200:
            raise ValueError(f"GitHub repo lookup failed ({repo_resp.status_code})")
        default_branch = repo_resp.json().get("default_branch", "main")

        tree_resp = client.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}",
            params={"recursive": "1"},
        )
        if tree_resp.status_code != 200:
            raise ValueError(f"GitHub tree lookup failed ({tree_resp.status_code})")
        tree = tree_resp.json().get("tree", [])
        return [item["path"] for item in tree if item.get("type") == "blob"]
    finally:
        if own_client:
            client.close()


def inspect_repo_health(github_url: str) -> dict:
    parsed = parse_github_url(github_url)
    if not parsed:
        return {"issues": ["GitHub URL could not be parsed"], "file_count": 0, "paths": []}

    owner, repo = parsed
    try:
        paths = fetch_repo_tree(owner, repo)
    except Exception as exc:
        return {"issues": [f"Could not inspect repository: {exc}"], "file_count": 0, "paths": []}

    paths_l = [p.lower() for p in paths]
    issues = []

    if not any(any(hint in p for hint in TEST_PATH_HINTS) for p in paths_l):
        issues.append("Repository has no test files or test directory")
    if not any(any(hint in p for hint in CI_PATH_HINTS) for p in paths_l):
        issues.append("No CI/CD pipeline configuration found")
    if not any(any(hint in p for hint in DEPLOY_FILE_HINTS) for p in paths_l):
        issues.append("No deployment configuration found (Dockerfile, Procfile, etc.)")
    if not any(any(p == hint or p.endswith("/" + hint) for hint in README_HINTS) for p in paths_l):
        issues.append("No README found in the repository root")

    return {"issues": issues, "file_count": len(paths), "paths": paths}
