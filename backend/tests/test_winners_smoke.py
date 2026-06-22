import os

os.environ["DATABASE_URL"] = "sqlite:///./test_winners_smoke.db"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    if os.path.exists("test_winners_smoke.db"):
        os.remove("test_winners_smoke.db")
    from app.database import Base, engine
    from app.main import app
    # Other test modules share this process's module-level `engine` singleton
    # and may have deleted the file it was originally bound to — ensure our
    # tables exist regardless of import order.
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    engine.dispose()
    if os.path.exists("test_winners_smoke.db"):
        os.remove("test_winners_smoke.db")


def _organizer_headers(client):
    r = client.post("/api/auth/organizer/signup", json={"name": "Org", "email": "org@test.dev", "password": "pw123456"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['auth_token']}"}


def test_winners_hidden_until_revealed_then_ranks_correctly(client):
    org_headers = _organizer_headers(client)

    r = client.post("/api/hackathons", json={
        "name": "Winners Test Hack", "description": "d", "eligibility_criteria": "open",
        "mode": "online", "allow_judges": True, "allow_mentors": True,
    }, headers=org_headers)
    assert r.status_code == 200, r.text
    hackathon_id = r.json()["id"]

    # two participants -> two teams
    r = client.post(f"/api/hackathons/{hackathon_id}/register/participant", json={
        "name": "P1", "email": "p1@test.dev", "team_name": "TeamA", "consent_accepted": True,
    })
    assert r.status_code == 200, r.text
    r = client.post(f"/api/hackathons/{hackathon_id}/register/participant", json={
        "name": "P2", "email": "p2@test.dev", "team_name": "TeamB", "consent_accepted": True,
    })
    assert r.status_code == 200, r.text

    r = client.get(f"/api/hackathons/{hackathon_id}/teams", headers=org_headers)
    teams = {t["team_name"]: t["id"] for t in r.json()}
    team_a, team_b = teams["TeamA"], teams["TeamB"]

    # two reviewers: one harsh, one lenient, both score both teams
    r = client.post(f"/api/hackathons/{hackathon_id}/reviewers", json={
        "name": "Harsh Judge", "expertise": ["AI"], "role": "judge",
    }, headers=org_headers)
    harsh_id = r.json()["id"]
    r = client.post(f"/api/hackathons/{hackathon_id}/reviewers", json={
        "name": "Lenient Judge", "expertise": ["AI"], "role": "judge",
    }, headers=org_headers)
    lenient_id = r.json()["id"]

    # Harsh judge scores everyone low, lenient scores everyone high, but TeamA is better on both
    for reviewer_id, (score_a, score_b) in [
        (harsh_id, (40, 30)),
        (lenient_id, (90, 80)),
    ]:
        for team_id, score in [(team_a, score_a), (team_b, score_b)]:
            r = client.post(f"/api/hackathons/{hackathon_id}/scores", json={
                "reviewer_id": reviewer_id, "team_id": team_id, "score": score,
            }, headers=org_headers)
            assert r.status_code == 200, r.text

    # not revealed yet -> empty rankings, revealed=False
    r = client.get(f"/api/hackathons/{hackathon_id}/winners", headers=org_headers)
    assert r.status_code == 200, r.text
    assert r.json() == {"revealed": False, "revealed_at": None, "rankings": []}

    # non-organizer can't reveal
    r = client.post(f"/api/hackathons/{hackathon_id}/winners/reveal")
    assert r.status_code == 401  # no auth at all

    # organizer reveals
    r = client.post(f"/api/hackathons/{hackathon_id}/winners/reveal", headers=org_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["revealed"] is True
    assert body["revealed_at"] is not None
    assert [entry["team_name"] for entry in body["rankings"]] == ["TeamA", "TeamB"]
    assert body["rankings"][0]["rank"] == 1
    assert body["rankings"][1]["rank"] == 2

    # now anyone in-scope sees it revealed too
    r = client.get(f"/api/hackathons/{hackathon_id}/winners", headers=org_headers)
    assert r.json()["revealed"] is True
    assert len(r.json()["rankings"]) == 2
