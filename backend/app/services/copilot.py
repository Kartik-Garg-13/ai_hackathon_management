from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CONFIDENCE_FLOOR = 0.15

KNOWLEDGE_BASE = [
    {
        "question": "What are the team size rules?",
        "answer": "Teams must have between 2 and 5 members. Solo participation is not allowed.",
        "tags": ["rules", "team"],
    },
    {
        "question": "What is the hackathon schedule?",
        "answer": "Registration closes the night before kickoff. Hacking runs for 36 hours, followed by submission deadline and judging the next morning, with the awards ceremony in the evening.",
        "tags": ["schedule"],
    },
    {
        "question": "How do I submit my project?",
        "answer": "Submit through the platform's Project Submission page: a GitHub repo link, a short pitch deck, and a 2-minute demo video. Submissions close automatically at the deadline.",
        "tags": ["submission"],
    },
    {
        "question": "What are the judging criteria?",
        "answer": "Projects are judged on Innovation, Technical Complexity, Presentation Quality, and real-world Impact, each scored out of 10 by assigned judges.",
        "tags": ["judging"],
    },
    {
        "question": "Can I change my team after registering?",
        "answer": "Yes, team changes are allowed up until the hacking period starts. Contact an organizer to update your team roster.",
        "tags": ["team", "rules"],
    },
    {
        "question": "What should be in my pitch deck?",
        "answer": "Cover the problem statement, your solution, technical approach, a live demo or screenshots, and what's next for the project. Keep it under 10 slides.",
        "tags": ["faq", "submission"],
    },
    {
        "question": "How do I deploy a FastAPI application?",
        "answer": "The simplest path is `uvicorn app.main:app --host 0.0.0.0 --port 8000` on a small VM, or containerize it with Docker and deploy to Render, Railway, or AWS ECS for something more production-like.",
        "tags": ["dev", "fastapi", "deployment"],
    },
    {
        "question": "How do I use PostgreSQL in my project?",
        "answer": "Install `psycopg2-binary`, set a `DATABASE_URL` env var like `postgresql://user:pass@host:5432/dbname`, and point your ORM (SQLAlchemy, Prisma, etc.) at it. Most hosts (Render, Supabase, Railway) offer a free Postgres instance for hackathons.",
        "tags": ["dev", "postgresql", "database"],
    },
    {
        "question": "Can you suggest a project idea?",
        "answer": "Pick a problem you've personally run into this month — judges respond well to specific, lived-in problems over generic ones. If you want a domain to explore: accessibility tools, climate/sustainability tracking, or AI-assisted learning are all underexplored relative to how many teams build in fintech/healthcare.",
        "tags": ["ideas"],
    },
    {
        "question": "What happens if my team is inactive?",
        "answer": "Mentors get a heads-up if a team has had no activity for a while, just so they can check in — it's not a penalty, just a way to make sure no team is stuck without help.",
        "tags": ["faq", "burnout"],
    },
    {
        "question": "Who can I ask for help during the hackathon?",
        "answer": "Mentors are available throughout the event — check the Mentor tab for who's online and their area of expertise.",
        "tags": ["faq", "mentor"],
    },
    {
        "question": "How is plagiarism or reused code handled?",
        "answer": "Reusing your own pre-existing code is fine as long as you disclose it in your submission. Presenting someone else's project as new work will get a team disqualified.",
        "tags": ["rules", "faq"],
    },
]

_QUESTIONS = [entry["question"] for entry in KNOWLEDGE_BASE]


@dataclass
class CopilotResult:
    answer: str
    matched_question: str | None
    confidence: float


def ask(question: str) -> CopilotResult:
    if not question.strip():
        return CopilotResult(
            answer="Ask me something about the rules, schedule, submission process, or judging criteria.",
            matched_question=None,
            confidence=0.0,
        )

    corpus = _QUESTIONS + [question]
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(corpus)
    similarities = cosine_similarity(vectors[-1], vectors[:-1])[0]

    best_idx = int(similarities.argmax())
    best_score = float(similarities[best_idx])

    if best_score < CONFIDENCE_FLOOR:
        return CopilotResult(
            answer="I don't have an answer for that yet. Try asking about rules, the schedule, submission process, judging criteria, or common dev questions like deployment.",
            matched_question=None,
            confidence=round(best_score, 2),
        )

    return CopilotResult(
        answer=KNOWLEDGE_BASE[best_idx]["answer"],
        matched_question=KNOWLEDGE_BASE[best_idx]["question"],
        confidence=round(best_score, 2),
    )
