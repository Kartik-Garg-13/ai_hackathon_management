import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import NetworkField from "../components/NetworkField.jsx";
import BrandName from "../components/BrandName.jsx";
import GlassCard from "../components/GlassCard.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import { api } from "../api.js";
import { getSession, clearSession } from "../auth.js";
import "./MentorDashboardPage.css";

const FILTERS = ["Open", "Answered", "All"];

export default function MentorDashboardPage() {
  const navigate = useNavigate();
  const session = getSession();

  const [queries, setQueries] = useState([]);
  const [filter, setFilter] = useState("Open");
  const [selectedId, setSelectedId] = useState(null);
  const [replyText, setReplyText] = useState("");

  const [leaderboard, setLeaderboard] = useState([]);
  const [wellbeing, setWellbeing] = useState([]);
  const [showAllTeams, setShowAllTeams] = useState(false);
  const [allTeamsWellbeing, setAllTeamsWellbeing] = useState([]);
  const [error, setError] = useState(null);

  function statusOf(q) {
    return q.status === "answered" ? "answered" : "open";
  }

  async function refresh() {
    try {
      setError(null);
      setQueries(await api.listQueries());
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    refresh();
    api.mentorLeaderboard().then(setLeaderboard).catch(() => {});
    api.flaggedTeams().then(setWellbeing).catch(() => {});
    api.burnoutReport().then(setAllTeamsWellbeing).catch(() => {});
  }, []);

  function handleLogout() {
    clearSession();
    navigate("/");
  }

  function handleSelect(id) {
    setSelectedId(id);
    setReplyText("");
  }

  async function handleReply(e) {
    e.preventDefault();
    if (!replyText.trim() || !selectedId) return;
    try {
      await api.respondToQuery(selectedId, replyText.trim());
      setReplyText("");
      await refresh();
    } catch (e) {
      setError(e.message);
    }
  }

  const visible = queries.filter((q) => {
    if (filter === "Open") return statusOf(q) === "open";
    if (filter === "Answered") return statusOf(q) === "answered";
    return true;
  });

  const selected = queries.find((q) => q.id === selectedId) || null;

  return (
    <div className="mentor-dash">
      <header className="mentor-dash__header">
        <div className="mentor-dash__header-net"><NetworkField density={12} variant="active" /></div>
        <div className="mentor-dash__header-inner">
          <div className="mentor-dash__brand"><BrandName size="sm" /></div>
          <div className="mentor-dash__header-right">
            <div className="mentor-dash__name-badge">{session?.name}</div>
            <button className="mentor-dash__logout" onClick={handleLogout}>Log out</button>
          </div>
        </div>
      </header>

      <main className="mentor-dash__main">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <h1 className="mentor-dash__title">Questions from participants</h1>
          <p className="mentor-dash__sub">Pick up a question, reply, and help a team get unblocked.</p>
        </motion.div>

        {error && <div className="mentor-dash__empty">{error}</div>}

        <div className="mentor-dash__layout">
          <GlassCard tone="light" className="mentor-dash__inbox">
            <div className="mentor-dash__inbox-head">
              <span className="mentor-dash__inbox-title">Inbox</span>
              <div className="mentor-dash__filter-pill">
                {FILTERS.map((f) => (
                  <button key={f} className={`mentor-dash__filter-btn ${filter === f ? "mentor-dash__filter-btn--active" : ""}`} onClick={() => setFilter(f)}>
                    {f}
                  </button>
                ))}
              </div>
            </div>

            {visible.length === 0 && <div className="mentor-dash__empty">No {filter !== "All" ? filter.toLowerCase() : ""} questions right now.</div>}

            {visible.map((q) => (
              <button key={q.id} className={`mentor-dash__doubt-item ${selectedId === q.id ? "mentor-dash__doubt-item--active" : ""}`} onClick={() => handleSelect(q.id)}>
                <div className="mentor-dash__doubt-item-top">
                  <span className="mentor-dash__doubt-subject">[{q.category}]</span>
                  <span className={`mentor-dash__doubt-status mentor-dash__doubt-status--${statusOf(q)}`}>{statusOf(q)}</span>
                </div>
                <span className="mentor-dash__doubt-preview">{truncate(q.body, 90)}</span>
              </button>
            ))}
          </GlassCard>

          <GlassCard tone="light" className="mentor-dash__chat">
            {!selected && <div className="mentor-dash__empty-chat">Select a question from the inbox to read it and reply.</div>}
            {selected && (
              <>
                <div className="mentor-dash__chat-head">
                  <span className="mentor-dash__chat-title">[{selected.category}]</span>
                </div>
                <div className="mentor-dash__thread">
                  <div className="mentor-dash__bubble mentor-dash__bubble--participant">{selected.body}</div>
                  {selected.response && (
                    <div className="mentor-dash__bubble mentor-dash__bubble--mentor">
                      {selected.response}
                      {selected.rating != null && <div style={{ fontSize: 12, marginTop: 4 }}>Rated {selected.rating}/5</div>}
                    </div>
                  )}
                </div>
                {statusOf(selected) === "open" && (
                  <form className="mentor-dash__reply-form" onSubmit={handleReply}>
                    <textarea className="mentor-dash__reply-input" rows={2} placeholder="Write a reply to help this team…" value={replyText} onChange={(e) => setReplyText(e.target.value)} />
                    <button type="submit" className="mentor-dash__send-btn" disabled={!replyText.trim()}>Send</button>
                  </form>
                )}
              </>
            )}
          </GlassCard>
        </div>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.15 }} style={{ marginTop: 32 }}>
          <h2 className="mentor-dash__title" style={{ fontSize: 20 }}>Mentor leaderboard</h2>
          <GlassCard tone="light" className="mentor-dash__inbox">
            {leaderboard.map((m, i) => (
              <div key={m.mentor_id} className="mentor-dash__doubt-item" style={{ cursor: "default" }}>
                <div className="mentor-dash__doubt-item-top">
                  <span className="mentor-dash__doubt-subject">#{i + 1} {m.mentor_name}</span>
                </div>
                <span className="mentor-dash__doubt-preview">{m.summary}</span>
              </div>
            ))}
            {leaderboard.length === 0 && <div className="mentor-dash__empty">No mentors yet.</div>}
          </GlassCard>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.25 }} style={{ marginTop: 32 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <h2 className="mentor-dash__title" style={{ fontSize: 20 }}>
              {showAllTeams ? "All teams' wellbeing" : "Teams that may need a check-in"}
            </h2>
            <div className="mentor-dash__filter-pill">
              <button
                className={`mentor-dash__filter-btn ${!showAllTeams ? "mentor-dash__filter-btn--active" : ""}`}
                onClick={() => setShowAllTeams(false)}
              >
                Flagged only
              </button>
              <button
                className={`mentor-dash__filter-btn ${showAllTeams ? "mentor-dash__filter-btn--active" : ""}`}
                onClick={() => setShowAllTeams(true)}
              >
                All teams
              </button>
            </div>
          </div>
          <GlassCard tone="light" className="mentor-dash__inbox">
            {(showAllTeams ? allTeamsWellbeing : wellbeing).map((t) => (
              <div key={t.team_id} className="mentor-dash__doubt-item" style={{ cursor: "default" }}>
                <div className="mentor-dash__doubt-item-top">
                  <span className="mentor-dash__doubt-subject">{t.team_name}</span>
                  <RiskBadge level={t.burnout_risk_level} kind="bias" />
                </div>
                <span className="mentor-dash__doubt-preview">{t.summary}</span>
              </div>
            ))}
            {(showAllTeams ? allTeamsWellbeing : wellbeing).length === 0 && (
              <div className="mentor-dash__empty">{showAllTeams ? "No teams found." : "No teams flagged right now."}</div>
            )}
          </GlassCard>
        </motion.div>
      </main>
    </div>
  );
}

function truncate(text, len) {
  if (!text) return "";
  return text.length > len ? `${text.slice(0, len)}…` : text;
}
