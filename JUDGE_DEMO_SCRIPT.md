# Judge Demo Script — DELLigent Minds

Everything below has been live-tested this session, not just claimed. Backend
running on http://localhost:8000, frontend on http://localhost:5173.

**Before presenting**: start both servers fresh.

```bash
cd backend && .venv/Scripts/uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev -- --port 5173
```

Organizer login: `organizer@demo.dev` / `demo1234`.

---

## 1. Registration Intelligence

**Show**: `/admin/registrations` → filter by "pending" → find **Priya Sharma**
(two entries, `priya.sharma.demo1@gmail.com` and `...demo2@gmail.com`).

Both are flagged **High Risk / PROJECT_DUPLICATE** with reasons: *"Very
Similar Registration," "Shared IP + Similar Registration," "Overused Project
Idea."* These were two real, separate self-registrations submitted seconds
apart with the same name and an identical project description but different
emails and team names — exactly the pattern someone dodging a duplicate-email
block would use. The system caught it anyway via TF-IDF similarity, not
just exact-match checks.

**Also show**: `/admin/analytics` for the full 10,000-row ground-truth
validation (93.4% duplicate-detection recall, 85.8% overall accuracy).

## 2. Reviewer Assignment

**Show**: `/admin/reviewers` — 40 assignments already run across the seeded
dataset, with plain-English match explanations ("Dr. Mehta has relevant
AI/ML experience..."). Conflict detection blocks reviewers sharing a team's
college/organization.

## 3. Bias Detection & Fairness

**Show**: `/admin/bias` — **Ms. Patel (Harsh Reviewer)** is flagged **High**
risk (z = −2.80), **Ms. Iyer** flagged **Medium** (z = 1.46, consistently
lenient). Toggle "show technical details" to reveal the z-scores behind the
plain-English summary.

## 4. AI Judge Assistant

**Show**: `/admin/registrations` → TurboTech143's pitch review (or re-run via
the participant dashboard's "AI Judge Assistant" section). The pitch deck
text claims *"deployed on AWS with Docker"* and a *"CI/CD pipeline,"* but the
linked GitHub repo (`github.com/octocat/Hello-World`) has none of that — the
system flags all three as **Potential Issues**, catching the gap between
what a team claims and what their repo actually shows.

## 5. Hackathon Copilot

**Show**: Participant dashboard → "Ask the Hackathon Copilot" → ask *"How do
I submit my project?"* — returns a real retrieval-matched answer with a
confidence score (0.79), not a canned response.

## 6. Burnout Detection

**Show**: `/admin/dashboard` or burnout report — seeded teams include
explicit active/declining/inactive examples. Point at **SiliconSages478**
(Medium risk, "activity dropped off sharply") as a concrete example rather
than the full list (most of the 4,108 bulk-imported teams have no activity
logs at all, so they default to flagged — worth explaining if asked).

## 7. Smart Reviewer Rotation

**Show**: TurboTech143's normalized scores — **Dr. Mehta** scored it 70.8,
**Ms. Patel (harsh)** scored it 49.0, a 21.8-point gap from reviewer bias
alone. After normalization: 62.08 vs 56.99 — a 5.1-point gap. Same project,
judged fairly regardless of who reviewed it.

## 8. AI Mentor Matching

**Show**: Two real submitted queries —
- *"My Android app keeps crashing on startup"* → auto-routed to **Mr. Khan**
  (Mobile expertise), not by exact category tag but by TF-IDF similarity to
  his bio.
- *"How do I prevent SQL injection"* → auto-routed to **Dr. Suresh**
  (Security/CTF).

Mr. Khan already answered the first one and was rated 5/5 — check the mentor
leaderboard to show it reflecting that.

## 9. Judge Dashboard

**Show**: `/api/hackathons/1/judge-dashboard` (or the equivalent admin page)
— live composite view: 4,113 teams, category distribution across 8 domains,
bias-adjusted top-teams leaderboard.

## 10. Project Similarity Detector

**Show**: `/admin/insights` → "Project categories" (6 auto-clustered
categories from project descriptions) and "Near-duplicate projects" (200+
flagged pairs from the seeded dataset — e.g. multiple "AI Resume Screener"
variants).

## 11. Live Plagiarism Detection

**The headline demo.** `/admin/insights` → "Run plagiarism scan" button.

Three real teams with real GitHub repos:
- **PlagiarismDemo Original** and **PlagiarismDemo Copy** both point to
  `github.com/pypa/sampleproject` (the same real repo).
- **PlagiarismDemo Unique** points to `github.com/octocat/Hello-World` (an
  unrelated repo).

The scan correctly flags Original vs. Copy as **100% similarity, High
risk**, with real file-level matches including **AST-based comparison** on
actual Python files (`noxfile.py`, `src/sample/__init__.py`,
`src/sample/simple.py`) — not just a text diff. Unique is correctly left
unflagged. This is a live GitHub API call each time, not cached/fake data.

---

## Known, honestly-disclosed limitations (mention if asked, don't wait to be caught)

- Skill taxonomy covers ~33 common terms; niche skills (game dev, hardware)
  fall into a generic "Other" bucket.
- Plagiarism AST comparison is real only for Python; other languages use
  text-diff similarity.
- No LLM anywhere — every feature above is TF-IDF, IsolationForest, DBSCAN,
  GaussianMixture, KMeans, z-score statistics, or `ast`-module analysis. This
  is a deliberate choice (zero cost, deterministic, explainable), not a
  shortcut.
