# AI Hackathon Platform — Core 3 AI Features

An AI-powered hackathon management platform implementing the **3 judged core AI
features**: Registration Intelligence, Reviewer Assignment Intelligence, and
Bias Detection & Fairness Engine. Built as a FastAPI + SQLite backend with a
minimal React frontend.

## Scope

This pass implements:

1. **Registration Intelligence** — duplicate/fraud detection, email & phone
   validation, skill/project alignment, trust scoring, explainable reasons,
   ground-truth evaluation. Ported from the original `Untitled2.ipynb`
   exploration notebook into `backend/app/services/registration_intelligence.py`
   — same algorithms, now callable from an API.
2. **Reviewer Assignment Intelligence** — TF-IDF/cosine matching of reviewer
   expertise to project requirements, conflict-of-interest blocking, and
   load-balanced greedy assignment.
3. **Bias Detection & Fairness Engine** — leave-one-out z-score analysis per
   reviewer, IQR outlier detection within a reviewer's own scores, a combined
   bias risk level + confidence, and an immutable audit trail.

**Deliberately out of scope for this pass:** the code workspace, chatbot,
judge assistant, project-similarity/plagiarism detectors, mentor matching,
burnout detection, and the broader admin panel (event builder, sponsor
management, trend engine). The API/DB/service-layer pattern established here
(FastAPI router → service module → SQLAlchemy model) generalizes directly to
those features without re-architecting.

## Architecture

```
backend/
  app/
    main.py                # FastAPI app, CORS, routers
    database.py            # SQLAlchemy engine (DATABASE_URL env var)
    models.py               # Team, Participant, Reviewer, Assignment, Score, AuditLog
    schemas.py               # Pydantic request/response models
    services/
      registration_intelligence.py   # ported notebook logic
      skill_taxonomy.py               # shared by features 1 & 2
      reviewer_assignment.py          # TF-IDF matching, conflicts, load balancing
      bias_detection.py                # z-score/IQR fairness engine
    api/
      registrations.py
      reviewers.py
      bias.py
  scripts/seed_demo_data.py  # loads sample_data/test.csv + synthetic reviewers/scores
  tests/                      # pytest unit + API smoke tests
frontend/                    # Vite + React, minimal CSS, 3 pages
sample_data/test.csv         # 10,000-row synthetic registration dataset with ground truth labels
```

Database uses only cross-dialect SQLAlchemy types (`JSON`, `String`, `Float`,
`Integer`, `DateTime`), so switching from SQLite to Postgres later is just
changing `DATABASE_URL` — no model changes required.

## Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # or source .venv/bin/activate on Linux/Mac
pip install -r requirements.txt
python scripts/seed_demo_data.py   # seeds DB with sample_data/test.csv + demo reviewers/scores
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # points at http://localhost:8000 by default
npm run dev
```

Open http://localhost:5173

### Docker

```bash
docker compose up --build
```

Backend on :8000, frontend on :4173. SQLite file persists in the
`backend_data` volume.

## API overview

| Feature | Endpoints |
|---|---|
| Registration Intelligence | `POST /api/registrations/upload`, `GET /api/registrations`, `GET /api/registrations/{id}`, `GET /api/registrations/analytics` |
| Reviewer Assignment | `POST /api/reviewers`, `GET /api/reviewers`, `POST /api/reviewers/assign`, `GET /api/reviewers/assignments` |
| Bias Detection | `POST /api/scores`, `GET /api/bias/reviewers`, `GET /api/bias/flagged`, `GET /api/audit-log` |

Full interactive docs (OpenAPI/Swagger) at `/docs` once the backend is running.

## Testing

```bash
cd backend
pytest -v
```

21 tests: unit tests for each service (registration scoring against known
fixtures, reviewer conflict/load-balancing logic, bias z-score math) plus
FastAPI `TestClient` smoke tests exercising upload → assign → score → bias
report end-to-end.

## Verified results (full 10,000-row sample dataset)

- Registration Intelligence: 85.8% accuracy, 0.71 macro F1, 0.93 ROC-AUC vs.
  ground truth labels; full pipeline runs in ~32s for 10,000 rows.
- Reviewer Assignment: conflict detection correctly excludes reviewers sharing
  a team's college/organization; load balancing distributes assignments
  evenly across capacity.
- Bias Detection: a seeded reviewer scoring ~20 points below the population
  mean is correctly flagged "High" bias risk (z ≈ -2.85).

## Notes for the team building the final frontend

The React app is intentionally thin — 3 page components, no business logic,
calling the JSON API directly via `frontend/src/api.js`. Swap the UI without
touching the backend; the API contract (`schemas.py`) is the integration
point.
