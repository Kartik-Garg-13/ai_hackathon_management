from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, bias, burnout, chat, copilot, dashboard, hackathons, invites, me, pitch, plagiarism, queries, registrations, reviewers, similarity, teams
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Hackathon Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(hackathons.router)
app.include_router(invites.router)
app.include_router(invites.invite_router)
app.include_router(registrations.router)
app.include_router(reviewers.router)
app.include_router(bias.router)
app.include_router(bias.scores_router)
app.include_router(bias.audit_router)
app.include_router(bias.teams_router)
app.include_router(pitch.router)
app.include_router(copilot.router)
app.include_router(burnout.router)
app.include_router(burnout.activity_router)
app.include_router(chat.router)
app.include_router(chat.ws_router)
app.include_router(queries.router)
app.include_router(queries.leaderboard_router)
app.include_router(dashboard.router)
app.include_router(me.router)
app.include_router(teams.router)
app.include_router(similarity.router)
app.include_router(plagiarism.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
