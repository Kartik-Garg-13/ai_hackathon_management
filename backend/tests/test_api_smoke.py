import io
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_smoke.db"

import pytest
from fastapi.testclient import TestClient

CSV_CONTENT = b"""id,name,email,college,skills,project_idea,team_name,ground_truth_label,phone_number
T1_001,Aman Gupta,amangupta1@gmail.com,IIT Delhi,"Python,React,FastAPI",AI Resume Screener,Alpha1,GENUINE,+919876543210
T1_002,Riya Shah,riyashah2@gmail.com,IIT Delhi,"Python,TensorFlow,NLP",AI Resume Screener,Alpha1,GENUINE,+919876543211
T2_001,Karan Verma,karanverma3@yahoo.com,NIT Trichy,"React,Node.js,JavaScript",Web Portal for Farmers,Beta2,GENUINE,+919876543212
"""


@pytest.fixture(scope="module")
def client():
    if os.path.exists("test_smoke.db"):
        os.remove("test_smoke.db")
    from app.database import engine
    from app.main import app
    with TestClient(app) as c:
        yield c
    engine.dispose()
    if os.path.exists("test_smoke.db"):
        os.remove("test_smoke.db")


@pytest.fixture(scope="module")
def auth_headers(client):
    resp = client.post("/api/auth/organizer/signup", json={
        "name": "Test Organizer", "email": "organizer@test.dev", "password": "testpass123",
    })
    token = resp.json()["auth_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/hackathons", json={"name": "Test Hackathon"}, headers=headers)
    hackathon_id = resp.json()["id"]

    return headers, hackathon_id


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_registration_upload_and_list(client, auth_headers):
    headers, hackathon_id = auth_headers
    resp = client.post(
        f"/api/hackathons/{hackathon_id}/registrations/upload",
        files={"file": ("test.csv", io.BytesIO(CSV_CONTENT), "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["rows_ingested"] == 3

    resp = client.get(f"/api/hackathons/{hackathon_id}/registrations", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 3

    resp = client.get(f"/api/hackathons/{hackathon_id}/registrations/analytics", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total_registrations"] == 3


def test_reviewer_create_and_assign(client, auth_headers):
    headers, hackathon_id = auth_headers
    resp = client.post(f"/api/hackathons/{hackathon_id}/reviewers", json={
        "name": "Dr. Test", "expertise": ["AI/ML", "Backend"], "organization": "Org X", "max_load": 5,
    }, headers=headers)
    assert resp.status_code == 200

    resp = client.post(f"/api/hackathons/{hackathon_id}/reviewers/assign", headers=headers)
    assert resp.status_code == 200
    assignments = resp.json()
    assert len(assignments) > 0


def test_score_submission_and_bias_report(client, auth_headers):
    headers, hackathon_id = auth_headers
    assignments = client.get(f"/api/hackathons/{hackathon_id}/reviewers/assignments", headers=headers).json()
    reviewer_id = assignments[0]["reviewer_id"]
    team_id = assignments[0]["team_id"]

    for score in [70, 72, 68, 74]:
        resp = client.post(f"/api/hackathons/{hackathon_id}/scores", json={
            "reviewer_id": reviewer_id, "team_id": team_id, "score": score,
        }, headers=headers)
        assert resp.status_code == 200

    resp = client.get(f"/api/hackathons/{hackathon_id}/bias/reviewers", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) > 0

    resp = client.get(f"/api/hackathons/{hackathon_id}/audit-log", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 4


def test_cross_hackathon_access_is_rejected(client, auth_headers):
    headers, hackathon_id = auth_headers
    other_hackathon_id = hackathon_id + 999
    resp = client.get(f"/api/hackathons/{other_hackathon_id}/bias/reviewers", headers=headers)
    assert resp.status_code in (403, 404)

    resp = client.get(f"/api/hackathons/{hackathon_id}/bias/reviewers")
    assert resp.status_code == 401


def test_me_endpoint_returns_role_appropriate_profile(client, auth_headers):
    headers, hackathon_id = auth_headers
    resp = client.get(f"/api/hackathons/{hackathon_id}/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "organizer"

    reg_resp = client.post(f"/api/hackathons/{hackathon_id}/register/participant", json={
        "name": "Me Tester", "email": "metester@example.dev", "consent_accepted": True,
    })
    participant_headers = {"Authorization": f"Bearer {reg_resp.json()['auth_token']}"}

    resp = client.get(f"/api/hackathons/{hackathon_id}/me", headers=participant_headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "participant"
    assert resp.json()["email"] == "metester@example.dev"


def test_invite_link_flow(client, auth_headers):
    headers, hackathon_id = auth_headers
    resp = client.post(f"/api/hackathons/{hackathon_id}/invite-links/generate", headers=headers)
    assert resp.status_code == 200
    links = {l["role"]: l["token"] for l in resp.json()}
    assert "judge" in links and "participant" not in links

    resp = client.get(f"/api/invite/{links['judge']}")
    assert resp.status_code == 200
    assert resp.json()["role"] == "judge"

    resp = client.post(f"/api/hackathons/{hackathon_id}/register/participant", json={
        "name": "Self Registered", "email": "self@registered.dev", "consent_accepted": True,
    })
    assert resp.status_code == 200
    assert resp.json()["role"] == "participant"


def test_open_hackathons_are_publicly_listed(client, auth_headers):
    headers, hackathon_id = auth_headers
    resp = client.get("/api/hackathons/public")
    assert resp.status_code == 200
    assert any(h["id"] == hackathon_id for h in resp.json())


def test_mentor_can_self_register_without_invite(client, auth_headers):
    headers, hackathon_id = auth_headers
    resp = client.post(f"/api/hackathons/{hackathon_id}/register/mentor", json={
        "name": "Open Mentor", "email": "open.mentor@example.dev", "expertise": ["Backend"],
    })
    assert resp.status_code == 200
    assert resp.json()["role"] == "mentor"


def test_participant_registration_requires_consent(client, auth_headers):
    headers, hackathon_id = auth_headers
    resp = client.post(f"/api/hackathons/{hackathon_id}/register/participant", json={
        "name": "No Consent", "email": "noconsent@example.dev", "consent_accepted": False,
    })
    assert resp.status_code == 400


def test_duplicate_judge_email_is_rejected(client, auth_headers):
    headers, hackathon_id = auth_headers
    links_resp = client.get(f"/api/hackathons/{hackathon_id}/invite-links", headers=headers)
    judge_token = next(l["token"] for l in links_resp.json() if l["role"] == "judge")

    payload = {"name": "Judge One", "email": "judge.dup@example.dev", "expertise": ["AI/ML"]}
    resp = client.post(f"/api/invite/{judge_token}/register/reviewer", json=payload)
    assert resp.status_code == 200

    payload2 = {"name": "Judge Two", "email": "judge.dup@example.dev", "expertise": ["Backend"]}
    resp = client.post(f"/api/invite/{judge_token}/register/reviewer", json=payload2)
    assert resp.status_code == 400


def test_registration_closed_after_deadline(client):
    resp = client.post("/api/auth/organizer/signup", json={
        "name": "Deadline Organizer", "email": "deadline_org@test.dev", "password": "testpass123",
    })
    headers = {"Authorization": f"Bearer {resp.json()['auth_token']}"}

    resp = client.post("/api/hackathons", json={
        "name": "Past Deadline Hackathon",
        "registration_deadline": "2020-01-01T00:00:00",
    }, headers=headers)
    hackathon_id = resp.json()["id"]

    resp = client.post(f"/api/hackathons/{hackathon_id}/register/participant", json={
        "name": "Too Late", "email": "toolate@example.dev", "consent_accepted": True,
    })
    assert resp.status_code == 400


def test_self_registration_is_pending_until_reanalyzed_then_approval_workflow(client, auth_headers):
    headers, hackathon_id = auth_headers

    resp = client.post(f"/api/hackathons/{hackathon_id}/register/participant", json={
        "name": "Pending Tester", "email": "pendingtester@example.dev", "team_name": "Alpha1",
        "skills": "Python,React,FastAPI", "project_idea": "AI Resume Screener", "consent_accepted": True,
    })
    assert resp.status_code == 200
    participant_token_auth = resp.json()["auth_token"]
    participant_headers = {"Authorization": f"Bearer {participant_token_auth}"}

    # Approval is still pending organizer review, but risk analysis itself now
    # runs immediately on registration (re-scored against the full population)
    # rather than waiting for an explicit reanalyze trigger.
    resp = client.get(f"/api/hackathons/{hackathon_id}/registrations", headers=headers, params={"approval_status": "pending"})
    assert resp.status_code == 200
    pending = [r for r in resp.json() if r["email"] == "pendingtester@example.dev"]
    assert len(pending) == 1
    assert pending[0]["final_trust_score"] is not None

    # Re-analyze All remains available for the organizer to manually re-run later.
    resp = client.post(f"/api/hackathons/{hackathon_id}/registrations/reanalyze", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["participants_analyzed"] >= 4

    resp = client.get(f"/api/hackathons/{hackathon_id}/registrations", headers=headers, params={"limit": 500})
    reanalyzed = next(r for r in resp.json() if r["email"] == "pendingtester@example.dev")
    assert reanalyzed["final_trust_score"] is not None

    resp = client.get(f"/api/hackathons/{hackathon_id}/bias/reviewers", headers=participant_headers)
    assert resp.status_code == 200

    resp = client.post(f"/api/hackathons/{hackathon_id}/registrations/{reanalyzed['id']}/reject", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["approval_status"] == "rejected"

    resp = client.get(f"/api/hackathons/{hackathon_id}/bias/reviewers", headers=participant_headers)
    assert resp.status_code == 401


def test_team_links_can_be_set_by_organizer(client, auth_headers):
    headers, hackathon_id = auth_headers
    resp = client.get(f"/api/hackathons/{hackathon_id}/teams", headers=headers)
    assert resp.status_code == 200
    team_id = resp.json()[0]["id"]

    resp = client.patch(
        f"/api/hackathons/{hackathon_id}/teams/{team_id}/links",
        json={"github_repo_url": "https://github.com/octocat/hello-world", "demo_video_url": "https://youtu.be/demo"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["github_repo_url"] == "https://github.com/octocat/hello-world"


def test_similarity_report_flags_near_duplicate_projects(client):
    resp = client.post("/api/auth/organizer/signup", json={
        "name": "Similarity Organizer", "email": "similarity_org@test.dev", "password": "testpass123",
    })
    headers = {"Authorization": f"Bearer {resp.json()['auth_token']}"}
    resp = client.post("/api/hackathons", json={"name": "Similarity Hackathon"}, headers=headers)
    hackathon_id = resp.json()["id"]

    csv = (
        "id,name,email,college,skills,project_idea,team_name,ground_truth_label,phone_number\n"
        "S1,Anu,anu@gmail.com,X,Python,AI Resume Screener for recruiters,Alpha,GENUINE,+910000000001\n"
        "S2,Bala,bala@gmail.com,X,Python,AI Resume Analyzer for recruiters,Beta,GENUINE,+910000000002\n"
        "S3,Cara,cara@gmail.com,X,React,Smart irrigation system for farmers,Gamma,GENUINE,+910000000003\n"
    ).encode()
    resp = client.post(
        f"/api/hackathons/{hackathon_id}/registrations/upload",
        files={"file": ("test.csv", io.BytesIO(csv), "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 200

    resp = client.get(f"/api/hackathons/{hackathon_id}/similarity/report", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["duplicate_pairs"]) >= 1
    assert {p["team_a_name"] for p in body["duplicate_pairs"]} | {p["team_b_name"] for p in body["duplicate_pairs"]} >= {"Alpha", "Beta"}


def test_mentor_query_routes_to_relevant_mentor_via_tfidf(client):
    resp = client.post("/api/auth/organizer/signup", json={
        "name": "Mentor Match Organizer", "email": "mentor_match_org@test.dev", "password": "testpass123",
    })
    headers = {"Authorization": f"Bearer {resp.json()['auth_token']}"}
    resp = client.post("/api/hackathons", json={"name": "Mentor Match Hackathon"}, headers=headers)
    hackathon_id = resp.json()["id"]

    react_mentor = client.post(f"/api/hackathons/{hackathon_id}/register/mentor", json={
        "name": "React Mentor", "email": "react.mentor@test.dev", "expertise": ["Frontend"],
        "bio": "React and JavaScript UI specialist",
    }).json()
    ml_mentor = client.post(f"/api/hackathons/{hackathon_id}/register/mentor", json={
        "name": "ML Mentor", "email": "ml.mentor@test.dev", "expertise": ["AI/ML"],
        "bio": "Machine learning, TensorFlow, and NLP specialist",
    }).json()

    participant = client.post(f"/api/hackathons/{hackathon_id}/register/participant", json={
        "name": "Asker", "email": "asker@test.dev", "consent_accepted": True,
    }).json()
    participant_headers = {"Authorization": f"Bearer {participant['auth_token']}"}

    resp = client.post(
        f"/api/hackathons/{hackathon_id}/queries",
        json={"category": "Frontend", "body": "Need help with React component re-renders"},
        headers=participant_headers,
    )
    assert resp.status_code == 200
    query = resp.json()
    react_reviewer_id = client.get(f"/api/hackathons/{hackathon_id}/me", headers={"Authorization": f"Bearer {react_mentor['auth_token']}"}).json()
    assert query["assigned_mentor_id"] == react_reviewer_id["id"]
