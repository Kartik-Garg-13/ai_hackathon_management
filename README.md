# DELLigent Minds — AI Hackathon Platform

A multi-tenant hackathon management platform covering the full event
lifecycle — registration, judging, mentoring, and live oversight — with 11
AI features built entirely on classical ML and statistics. No LLM API key
anywhere in the stack: every "AI" feature is TF-IDF, cosine similarity,
IsolationForest, DBSCAN, GaussianMixture, KMeans, z-score statistics, or
`ast`-module structural analysis.

Started from a single Jupyter notebook (`Untitled2.ipynb`) doing fraud
detection on a CSV of registrations; grew into a full FastAPI backend +
React frontend with real multi-tenant auth and four distinct roles.

## The 11 AI features

1. **Registration Intelligence** — exact/fuzzy-name/email-typo/near-duplicate
   detection (TF-IDF + GMM), IsolationForest anomaly scoring, DBSCAN
   fraud-ring grouping, shared-IP and duplicate-GitHub-username signals,
   final trust score with a plain-English explanation.
2. **Reviewer Assignment** — TF-IDF matching of judge expertise to project
   domain, fuzzy conflict detection (shared college/org), load-balanced
   greedy assignment.
3. **Bias Detection & Fairness** — leave-one-out z-score vs. population,
   IQR outlier detection, plain-English summaries.
4. **AI Judge Assistant** — combines pitch-deck scoring (innovation/
   technical/presentation) with a live GitHub repo health check (tests, CI,
   deployment config, README).
5. **Hackathon Copilot** — retrieval-only TF-IDF FAQ assistant; explicitly
   not generative, with an honest fallback when there's no good match.
6. **Burnout Detection** — activity-trend heuristics flag teams going quiet.
7. **Smart Reviewer Rotation** — rescales scores against each reviewer's own
   tendency so a harsh and a lenient reviewer converge toward a fair value.
8. **AI Mentor Matching** — TF-IDF similarity between a participant's
   question and mentor expertise/bio, with load-balanced fallback.
9. **Judge Dashboard** — live composite view: team counts, active/inactive
   split, category distribution, bias-adjusted leaderboard.
10. **Project Similarity Detector** — TF-IDF + cosine similarity flags
    near-duplicate project ideas; KMeans clusters all projects into labeled
    categories with counts.
11. **Live Plagiarism Detection** — fetches teams' GitHub repos live via the
    GitHub API; real `ast`-module structural comparison for Python files,
    text-diff similarity for other languages, plus commit-history stats.

## Architecture

```
backend/
  app/
    main.py                       # FastAPI app, CORS, router registration
    database.py                   # SQLAlchemy engine (DATABASE_URL env var)
    auth.py                       # stdlib-only auth — PBKDF2 + opaque tokens
    models.py                     # Hackathon, Team, Participant, Reviewer, Score, ...
    schemas.py                    # Pydantic request/response models
    services/
      registration_intelligence.py  # fraud/duplicate detection
      skill_taxonomy.py             # shared skill/category taxonomy
      reviewer_assignment.py        # TF-IDF matching, conflicts, load balancing
      bias_detection.py             # z-score/IQR fairness engine
      pitch_analyzer.py             # pitch deck scoring
      repo_inspector.py             # GitHub repo health checks
      similarity_detector.py        # project similarity + clustering
      plagiarism_detector.py        # GitHub repo AST/text comparison
      mentor_matcher.py             # TF-IDF mentor matching
      mentor_leaderboard.py
      burnout_detection.py
      copilot.py
    api/                          # one router module per feature area
  scripts/seed_demo_data.py       # loads sample_data/test.csv + synthetic reviewers/scores
  tests/                          # 75 pytest unit + API smoke tests
frontend/                         # Vite + React, role-based dashboards
sample_data/test.csv              # 10,000-row synthetic registration dataset with ground truth labels
```

Database uses only cross-dialect SQLAlchemy types, so switching from SQLite
to Postgres later is just changing `DATABASE_URL` — no model changes
required. Every table is scoped by `hackathon_id`; one organizer can run
multiple hackathons.

## Roles & registration

- **Organizer** — creates hackathons, manages registrations, runs reviewer
  assignment, generates judge invite links.
- **Judge** — invite-link only, the one role that still requires organizer
  approval.
- **Mentor** and **Participant** — self-register to any open hackathon via
  `GET /api/hackathons/public`, no invite link required.

## Running locally

### Prerequisites

- Python 3.10+
- Node 18+
- Git

### 1. Clone the repo

```bash
git clone https://github.com/Kartik-Garg-13/ai_hackathon_management.git
cd ai_hackathon_management
```

### 2. Backend (terminal 1)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
python scripts/seed_demo_data.py   # wipes and reseeds the DB with demo data
uvicorn app.main:app --reload
```

Leave this running. API docs (interactive Swagger UI): http://localhost:8000/docs

The seed script prints the demo organizer credentials and a fresh judge
invite link every time it runs — re-run it any time you want to reset to a
clean demo state.

### 3. Frontend (terminal 2 — open a new terminal, keep the backend running)

```bash
cd frontend
npm install
npm run dev -- --port 5173
```

Open **http://localhost:5173** in your browser. That's the actual website.

### 4. Try it out

- **Organizer**: go to `/admin/login`, sign in with `organizer@demo.dev` /
  `demo1234` (printed by the seed script). From the dashboard you can browse
  registrations, run reviewer assignment, view bias reports, and check
  Project Insights (similarity + plagiarism detection).
- **Participant**: go to `/participant/login` — pick any open hackathon and
  register directly, no invite link needed.
- **Mentor**: go to `/mentor/login` — same self-registration flow.
- **Judge**: needs the invite link the seed script printed to your terminal
  (`/join/<token>`) — judges are the one role that still requires an
  organizer-issued invite.

### Docker (alternative to steps 2–3)

```bash
docker compose up --build
```

Builds and runs both services together — backend on :8000, frontend on
:4173. You'll still need to seed the database once (see step 2) inside the
running backend container, or run the seed script locally against the same
`DATABASE_URL` first.

### Troubleshooting

- **"Port already in use"**: another process is already bound to 8000 or
  5173 — stop it, or run with a different port (`--port 5174`,
  `uvicorn app.main:app --reload --port 8001`, and update
  `frontend/src/api.js`'s fallback URL or set `VITE_API_URL` to match).
- **Frontend loads but nothing works / network errors**: the backend isn't
  running, or isn't on the port the frontend expects (defaults to
  `http://localhost:8000`).
- **Want a clean slate**: re-run `python scripts/seed_demo_data.py` — it
  drops and recreates every table before reseeding.

## Testing

```bash
cd backend
pytest -v
```

75 tests: unit tests for each service (registration scoring, reviewer
conflict/load-balancing, bias z-score math, similarity/plagiarism
detection, mentor matching) plus FastAPI `TestClient` smoke tests exercising
full flows end-to-end — registration → reanalysis → reviewer assignment →
scoring → bias report.

## Verified results (live-tested, not estimated)

- Registration: a single new entry processes in ~0.3s (full duplicate/fraud
  pipeline); 93.4% recall on the full 10,000-row ground-truth dataset.
- Reviewer assignment: ~0.6s for the full seeded dataset (4,108 teams).
- Bias detection: 100% accuracy/recall/precision on a 20-reviewer synthetic
  benchmark (14 fair, 6 deliberately biased) after fixing a threshold bug
  that conflated within-reviewer score variance with population-level bias.
- Known, honestly-flagged limitations: skill taxonomy covers ~33 common
  terms (novel skills fall into a generic "Other" bucket); plagiarism AST
  comparison is real only for Python, text-diff for other languages; demo
  video URLs are stored but not AI-analyzed.

## Notes on the frontend

The React app uses a team-provided design system (Winter Network theme) with
real backend-driven logic underneath — no fake/localStorage auth anywhere.
Landing page features an interactive 3D brain visualization
(`frontend/src/components/BrainIntro.jsx`) showcasing all 11 features as
nodes in a procedurally-generated neural network, built with
`@react-three/fiber`.
