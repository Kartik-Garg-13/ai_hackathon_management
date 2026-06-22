import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import NetworkField from "../components/NetworkField.jsx";
import BrandName from "../components/BrandName.jsx";
import GlassCard from "../components/GlassCard.jsx";
import Button from "../components/Button.jsx";
import { TextField, TextAreaField } from "../components/Field.jsx";
import FeatureCard from "../components/FeatureCard.jsx";
import ProfileMenu from "../components/ProfileMenu.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import ChatPanel from "../components/ChatPanel.jsx";
import { api } from "../api.js";
import { getSession, clearSession } from "../auth.js";
import "./DashboardPage.css";

const CATEGORIES = ["AI/ML", "Frontend", "Backend", "Mobile", "Cloud/DevOps", "Data", "Security", "Programming", "Other"];

const FEATURES = [
  { id: "registration", accent: "registration", status: "Verified", title: "Your entry, checked instantly", description: "The moment you register, we double-check every field — format, duplicates, and completeness.", cta: "View my registration status", icon: <IconShield /> },
  { id: "reviewer", accent: "reviewer", status: "Matched", title: "Matched with the right judges", description: "Your project is paired with reviewers who fit its domain, with workload spread evenly.", cta: "See my review status", icon: <IconShuffle /> },
  { id: "bias", accent: "bias", status: "Protected", title: "Judged on merit, not luck", description: "Scores are watched in real time for skew across colleges, teams, or backgrounds.", cta: "View fairness report", icon: <IconScan /> },
  { id: "winner", accent: "winner", status: "Live soon", title: "Results, revealed together", description: "When judging wraps, final rankings drop for every participant at the same moment.", cta: "Preview the podium", icon: <IconTrophy /> },
];

export default function DashboardPage() {
  const navigate = useNavigate();
  const session = getSession();

  const [me, setMe] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);

  const [queryCategory, setQueryCategory] = useState(CATEGORIES[0]);
  const [queryBody, setQueryBody] = useState("");
  const [myQueries, setMyQueries] = useState([]);

  const [checkinNote, setCheckinNote] = useState("");
  const [checkinStatus, setCheckinStatus] = useState(null);

  const [pitchResult, setPitchResult] = useState(null);
  const [uploading, setUploading] = useState(false);

  const [githubUrl, setGithubUrl] = useState("");
  const [demoVideoUrl, setDemoVideoUrl] = useState("");
  const [savingLinks, setSavingLinks] = useState(false);
  const [linksSaved, setLinksSaved] = useState(false);

  const [error, setError] = useState(null);

  useEffect(() => {
    api.getMe().then(setMe).catch((e) => setError(e.message));
    refreshQueries();
  }, []);

  useEffect(() => {
    if (!me?.team_id) return;
    api.getPitchReview(me.team_id).then(setPitchResult).catch(() => {});
  }, [me?.team_id]);

  async function refreshQueries() {
    try {
      setMyQueries(await api.listQueries());
    } catch (e) {
      setError(e.message);
    }
  }

  function handleLogout() {
    clearSession();
    navigate("/");
  }

  async function handleAsk(e) {
    e.preventDefault();
    try {
      setError(null);
      setAnswer(await api.askCopilot(question));
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleAskMentor(e) {
    e.preventDefault();
    try {
      setError(null);
      await api.submitQuery({ category: queryCategory, body: queryBody });
      setQueryBody("");
      await refreshQueries();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleRate(queryId, rating) {
    try {
      await api.rateQuery(queryId, rating);
      await refreshQueries();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleCheckin(e) {
    e.preventDefault();
    try {
      setError(null);
      setCheckinStatus(null);
      await api.logActivity({ team_id: me.team_id, activity_type: "check_in", note: checkinNote || null });
      setCheckinStatus("Checked in — mentors will see your team as active.");
      setCheckinNote("");
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSaveLinks(e) {
    e.preventDefault();
    setSavingLinks(true);
    setLinksSaved(false);
    try {
      setError(null);
      await api.updateTeamLinks(me.team_id, { github_repo_url: githubUrl || null, demo_video_url: demoVideoUrl || null });
      setLinksSaved(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingLinks(false);
    }
  }

  async function handlePitchUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      setError(null);
      setPitchResult(await api.analyzePitch(me.team_id, file));
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  if (!me) {
    return (
      <div className="dashboard-page__status" style={{ padding: "3rem", textAlign: "center" }}>
        {error ? (
          <>
            <p>{error}</p>
            <button onClick={handleLogout} style={{ marginTop: 12, textDecoration: "underline", background: "none", border: "none", cursor: "pointer" }}>
              Log in again
            </button>
          </>
        ) : (
          "Loading your dashboard…"
        )}
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <header className="dashboard-page__header">
        <div className="dashboard-page__header-network"><NetworkField density={14} variant="active" /></div>
        <div className="dashboard-page__header-content">
          <div className="dashboard-page__brand"><BrandName size="sm" /></div>
          <ProfileMenu participant={me} onLogout={handleLogout} />
        </div>
      </header>

      <main className="dashboard-page__main">
        <motion.div className="dashboard-page__intro" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <span className="dashboard-page__eyebrow">24–48 hour challenge for innovators</span>
          <h1>Welcome back, <span className="dashboard-page__highlight">{firstName(me.name)}</span></h1>
        </motion.div>

        {error && <div className="dashboard-page__doubt-empty">{error}</div>}

        <motion.div className="dashboard-page__grid" initial="hidden" animate="show" variants={{ hidden: {}, show: { transition: { staggerChildren: 0.12, delayChildren: 0.15 } } }}>
          {FEATURES.map((feature) => (
            <motion.div key={feature.id} variants={{ hidden: { opacity: 0, y: 26 }, show: { opacity: 1, y: 0, transition: { duration: 0.55 } } }}>
              <FeatureCard feature={feature} />
            </motion.div>
          ))}
        </motion.div>

        <motion.div className="dashboard-page__doubts" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }}>
          <div className="dashboard-page__section-title">Your registration status</div>
          <GlassCard tone="light" className="dashboard-page__doubt-form-card">
            {me.final_risk_level ? (
              <p><RiskBadge level={me.final_risk_level} kind="registration" /></p>
            ) : (
              <p className="dashboard-page__doubt-empty">Not yet analyzed — the organizer hasn't run a full risk analysis since you joined.</p>
            )}
          </GlassCard>
        </motion.div>

        <ChatPanel />

        <motion.div className="dashboard-page__doubts" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.35 }}>
          <div className="dashboard-page__section-title">Ask a mentor</div>
          <div className="dashboard-page__doubts-grid">
            <GlassCard tone="light" className="dashboard-page__doubt-form-card">
              <form onSubmit={handleAskMentor} className="dashboard-page__doubt-form">
                <label className="dashboard-page__doubt-select-label">
                  Category
                  <select className="dashboard-page__doubt-select" value={queryCategory} onChange={(e) => setQueryCategory(e.target.value)}>
                    {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </label>
                <TextAreaField label="Your question" required rows={3} placeholder="Describe what you're stuck on…" value={queryBody} onChange={(e) => setQueryBody(e.target.value)} />
                <Button type="submit" variant="primary" size="md" disabled={!queryBody.trim()}>Send to mentors</Button>
              </form>
            </GlassCard>

            <div className="dashboard-page__doubt-list">
              {myQueries.length === 0 && <div className="dashboard-page__doubt-empty">No questions asked yet.</div>}
              {myQueries.map((q) => (
                <GlassCard key={q.id} tone="light" className="dashboard-page__doubt-item">
                  <div className="dashboard-page__doubt-item-top">
                    <span className="dashboard-page__doubt-item-subject">[{q.category}]</span>
                    <span className={`dashboard-page__doubt-item-status dashboard-page__doubt-item-status--${q.status}`}>
                      {q.status === "answered" ? "Answered" : "Awaiting reply"}
                    </span>
                  </div>
                  <p className="dashboard-page__doubt-item-message">{q.body}</p>
                  {q.response && (
                    <div className="dashboard-page__doubt-reply">
                      <strong>Mentor</strong>
                      <span>{q.response}</span>
                      {q.rating == null ? (
                        <div style={{ marginTop: 6 }}>
                          {[1, 2, 3, 4, 5].map((n) => (
                            <button key={n} onClick={() => handleRate(q.id, n)} style={{ marginRight: 4, cursor: "pointer" }}>{n}</button>
                          ))}
                        </div>
                      ) : (
                        <span style={{ fontSize: 12 }}>Rated {q.rating}/5</span>
                      )}
                    </div>
                  )}
                </GlassCard>
              ))}
            </div>
          </div>
        </motion.div>

        <motion.div className="dashboard-page__doubts" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.4 }}>
          <div className="dashboard-page__section-title">Ask the Hackathon Copilot</div>
          <GlassCard tone="light" className="dashboard-page__doubt-form-card">
            <form onSubmit={handleAsk} className="dashboard-page__doubt-form">
              <TextField label="Question" placeholder="e.g. How do I deploy FastAPI?" value={question} onChange={(e) => setQuestion(e.target.value)} />
              <Button type="submit" variant="primary" size="md">Ask</Button>
            </form>
            {answer && <p style={{ marginTop: 10 }}>{answer.answer}</p>}
          </GlassCard>
        </motion.div>

        {me.team_id ? (
          <>
            <motion.div className="dashboard-page__doubts" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.45 }}>
              <div className="dashboard-page__section-title">Check in</div>
              <GlassCard tone="light" className="dashboard-page__doubt-form-card">
                <form onSubmit={handleCheckin} className="dashboard-page__doubt-form">
                  <TextField label="What did you just do? (optional)" value={checkinNote} onChange={(e) => setCheckinNote(e.target.value)} />
                  <Button type="submit" variant="primary" size="md">Check In</Button>
                </form>
                {checkinStatus && <p style={{ marginTop: 8 }}>{checkinStatus}</p>}
              </GlassCard>
            </motion.div>

            <motion.div className="dashboard-page__doubts" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.5 }}>
              <div className="dashboard-page__section-title">AI Judge Assistant</div>
              <GlassCard tone="light" className="dashboard-page__doubt-form-card">
                <form onSubmit={handleSaveLinks} className="dashboard-page__doubt-form">
                  <TextField label="GitHub repo URL" placeholder="https://github.com/yourteam/project" value={githubUrl} onChange={(e) => setGithubUrl(e.target.value)} />
                  <TextField label="Demo video URL (optional)" placeholder="https://youtu.be/…" value={demoVideoUrl} onChange={(e) => setDemoVideoUrl(e.target.value)} />
                  <Button type="submit" variant="primary" size="md" loading={savingLinks}>Save links</Button>
                </form>
                {linksSaved && <p style={{ marginTop: 8 }}>Saved — judges will see repo health checks alongside your pitch deck review.</p>}

                <label
                  className={`dashboard-page__file-upload-label ${uploading ? "dashboard-page__file-upload-label--disabled" : ""}`}
                  style={{ marginTop: 16 }}
                >
                  {uploading ? "Analyzing…" : "Upload pitch deck (.pptx)"}
                  <input type="file" accept=".pptx" onChange={handlePitchUpload} style={{ display: "none" }} disabled={uploading} />
                </label>
                {pitchResult && (
                  <div style={{ marginTop: 10 }}>
                    <p>Innovation: {pitchResult.innovation_score}/10 | Technical: {pitchResult.technical_complexity} | Presentation: {pitchResult.presentation_quality}</p>
                    {pitchResult.issues.length > 0 ? (
                      <ul>{pitchResult.issues.map((issue, i) => <li key={i}>{issue}</li>)}</ul>
                    ) : (
                      <p className="dashboard-page__doubt-empty">No issues flagged.</p>
                    )}
                  </div>
                )}
              </GlassCard>
            </motion.div>
          </>
        ) : (
          <motion.div className="dashboard-page__doubts" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.45 }}>
            <GlassCard tone="light" className="dashboard-page__doubt-form-card">
              <p className="dashboard-page__doubt-empty">
                Check-in and pitch upload need your team to be linked by the organizer first — ask them to run a registration import if this doesn't update.
              </p>
            </GlassCard>
          </motion.div>
        )}
      </main>
    </div>
  );
}

function firstName(fullName) {
  return (fullName || "Participant").split(" ")[0];
}

function IconShield() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" /><path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}
function IconShuffle() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M3 6h4l8 12h4M17 6h4M17 18h4M14 6l3-3M14 6l3 3M17 18l3-3M17 18l3 3M3 18h4l4-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}
function IconScan() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M4 8V5a1 1 0 011-1h3M20 8V5a1 1 0 00-1-1h-3M4 16v3a1 1 0 001 1h3M20 16v3a1 1 0 01-1 1h-3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /><path d="M4 12h16" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg>;
}
function IconTrophy() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M7 4h10v5a5 5 0 01-10 0V4z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" /><path d="M7 5H4v2a3 3 0 003 3M17 5h3v2a3 3 0 01-3 3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /><path d="M12 14v3M9 20h6M10 17h4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg>;
}
