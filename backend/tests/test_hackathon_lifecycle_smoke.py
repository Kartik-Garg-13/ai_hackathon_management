import os

os.environ["DATABASE_URL"] = "sqlite:///./test_lifecycle_smoke.db"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    if os.path.exists("test_lifecycle_smoke.db"):
        os.remove("test_lifecycle_smoke.db")
    from app.database import Base, engine
    from app.main import app
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    engine.dispose()
    if os.path.exists("test_lifecycle_smoke.db"):
        os.remove("test_lifecycle_smoke.db")


def _organizer_headers(client):
    r = client.post("/api/auth/organizer/signup", json={"name": "Org", "email": "org@test.dev", "password": "pw123456"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['auth_token']}"}


def test_stop_resume_end_lifecycle_blocks_participant_writes(client):
    org_headers = _organizer_headers(client)

    r = client.post("/api/hackathons", json={
        "name": "Lifecycle Test Hack", "description": "d", "eligibility_criteria": "open",
        "mode": "online", "allow_judges": True, "allow_mentors": True,
    }, headers=org_headers)
    hackathon_id = r.json()["id"]
    assert r.json()["status"] == "active"

    r = client.post(f"/api/hackathons/{hackathon_id}/register/participant", json={
        "name": "P1", "email": "p1@test.dev", "team_name": "TeamA", "consent_accepted": True,
    })
    token = r.json()["auth_token"]
    part_headers = {"Authorization": f"Bearer {token}"}

    r = client.get(f"/api/hackathons/{hackathon_id}/teams", headers=org_headers)
    team_id = r.json()[0]["id"]

    # active: participant can update links
    r = client.patch(f"/api/hackathons/{hackathon_id}/teams/{team_id}/links", json={
        "github_repo_url": "https://github.com/octocat/Hello-World",
    }, headers=part_headers)
    assert r.status_code == 200, r.text

    # only organizer can stop
    r = client.post(f"/api/hackathons/{hackathon_id}/stop", headers=part_headers)
    assert r.status_code == 403, r.text

    r = client.post(f"/api/hackathons/{hackathon_id}/stop", headers=org_headers)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "stopped"

    # stopped: participant writes blocked
    r = client.patch(f"/api/hackathons/{hackathon_id}/teams/{team_id}/links", json={
        "github_repo_url": "https://github.com/octocat/Spoon-Knife",
    }, headers=part_headers)
    assert r.status_code == 403, r.text
    assert "locked" in r.json()["detail"]

    # but organizer can still edit while stopped
    r = client.patch(f"/api/hackathons/{hackathon_id}/teams/{team_id}/links", json={
        "demo_video_url": "https://youtu.be/abc",
    }, headers=org_headers)
    assert r.status_code == 200, r.text

    # can't double-stop
    r = client.post(f"/api/hackathons/{hackathon_id}/stop", headers=org_headers)
    assert r.status_code == 400

    # resume -> active again, participant writes allowed
    r = client.post(f"/api/hackathons/{hackathon_id}/resume", headers=org_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "active"

    r = client.patch(f"/api/hackathons/{hackathon_id}/teams/{team_id}/links", json={
        "github_repo_url": "https://github.com/octocat/Spoon-Knife",
    }, headers=part_headers)
    assert r.status_code == 200, r.text

    # end -> permanent, participant writes blocked, can't resume from ended
    r = client.post(f"/api/hackathons/{hackathon_id}/end", headers=org_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "ended"

    r = client.post(f"/api/hackathons/{hackathon_id}/resume", headers=org_headers)
    assert r.status_code == 400

    r = client.patch(f"/api/hackathons/{hackathon_id}/teams/{team_id}/links", json={
        "github_repo_url": "https://github.com/octocat/git-consortium",
    }, headers=part_headers)
    assert r.status_code == 403, r.text
