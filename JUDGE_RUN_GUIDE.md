# Running DELLigent Minds — Quick Guide for Judges

This is a full-stack hackathon management platform with 11 AI features —
**zero LLM calls, zero API keys**. Everything is classical ML (TF-IDF,
IsolationForest, DBSCAN, GaussianMixture, KMeans, z-score statistics, AST
code analysis). It runs entirely on your machine, no internet account or
secrets needed (one feature — live plagiarism scan — calls the public
GitHub API, no key required).

Two terminals, ~3 minutes to get running.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Git

## 1. Clone

```bash
git clone https://github.com/Kartik-Garg-13/ai_hackathon_management.git
cd ai_hackathon_management
```

## 2. Backend — Terminal 1

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
python scripts/seed_demo_data.py   # loads 10,000+ sample registrations, reviewers, scores
uvicorn app.main:app --reload
```

Leave this running. You should see `Uvicorn running on http://127.0.0.1:8000`.

Interactive API docs (optional, for inspecting endpoints directly):
**http://localhost:8000/docs**

The seed script prints organizer credentials and a judge invite link to
the terminal — you don't need to copy them, they're fixed values, listed below.

## 3. Frontend — Terminal 2 (new terminal, keep the backend running)

```bash
cd frontend
npm install
npm run dev -- --port 5173
```

Open **http://localhost:5173** — that's the website.

## 4. Log in and look around

| Role | URL | Credentials |
|---|---|---|
| Organizer | `/admin/login` | `organizer@demo.dev` / `demo1234` |
| Participant | `/participant/login` | Self-register — pick any open hackathon, no invite needed |
| Mentor | `/mentor/login` | Self-register, same flow as participant |
| Judge | needs an invite link printed in the backend terminal (`/join/<token>`) | — |

### What to click as Organizer (covers most of the 11 features)

1. **Dashboard → Registrations** — upload-CSV intelligence, risk flags,
   fraud-ring detection, search by name/team, accuracy metrics vs. ground
   truth (top of the page).
2. **Dashboard → Bias & Fairness** — reviewer bias z-scores, and the
   "Team score comparison" section showing each judge's raw score next to
   the bias-corrected normalized score for the same team.
3. **Dashboard → Project Insights** — project-idea clustering, near-duplicate
   detection, and a **live** plagiarism scan that pulls real GitHub repos
   and runs AST-level Python comparison (takes a few seconds — it's a real
   network call, not cached).
4. **Dashboard → Reviewers** — TF-IDF-based judge↔project matching and
   conflict-of-interest detection.

### What to click as Mentor

- Inbox of participant questions routed by topic similarity, mentor
  leaderboard, and a team-wellbeing/burnout view (toggle between
  "flagged only" and "all teams").

### What to click as Participant

- Self-register, ask the Hackathon Copilot a question (retrieval-only —
  it'll honestly say "I don't have a good answer" rather than hallucinate),
  upload a pitch deck for AI scoring against your linked GitHub repo.

## Resetting to a clean state

Re-run `python scripts/seed_demo_data.py` any time — it wipes and reloads
everything from scratch.

## Troubleshooting

- **"Port already in use"** — something else is on 8000 or 5173. Stop it,
  or run `npm run dev -- --port 5174` / `uvicorn app.main:app --reload --port 8001`
  and set `VITE_API_URL` in the frontend to match.
- **Frontend shows a blank "No active hackathon" type error** — log out and
  back in as organizer, then click "Manage" on the hackathon card.
- **Plagiarism scan is slow or returns nothing** — it's a live GitHub API
  call per team; flaky internet or GitHub rate limits can affect it. Re-run
  the scan if it stalls.

## Automated tests

```bash
cd backend
.venv/Scripts/activate
pytest -v
```

75 tests covering fraud detection, bias correction, plagiarism, mentor
matching, and the full API surface — all passing as of submission.
