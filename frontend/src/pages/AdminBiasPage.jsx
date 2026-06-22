import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import GlassCard from "../components/GlassCard.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import { api } from "../api.js";
import "./AdminBiasPage.css";

export default function AdminBiasPage() {
  const navigate = useNavigate();

  const [bias, setBias] = useState([]);
  const [biasLoading, setBiasLoading] = useState(true);
  const [biasError, setBiasError] = useState(null);

  const [flagged, setFlagged] = useState([]);
  const [flaggedLoading, setFlaggedLoading] = useState(true);

  const [audit, setAudit] = useState([]);
  const [auditLoading, setAuditLoading] = useState(true);

  const [teams, setTeams] = useState([]);
  const [selectedTeamId, setSelectedTeamId] = useState(null);
  const [normalized, setNormalized] = useState([]);
  const [normalizedLoading, setNormalizedLoading] = useState(false);
  const [normalizedError, setNormalizedError] = useState(null);

  const [openDetails, setOpenDetails] = useState({});

  const teamNameById = Object.fromEntries(teams.map((t) => [t.id, t.team_name]));

  useEffect(() => {
    api.biasReport().then(setBias).catch((e) => setBiasError(e.message)).finally(() => setBiasLoading(false));
    api.flaggedReviewers().then(setFlagged).finally(() => setFlaggedLoading(false));
    api.auditLog()
      .then((data) => setAudit([...data].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))))
      .finally(() => setAuditLoading(false));
    api.listTeams().then((data) => {
      setTeams(data);
      if (data.length > 0) setSelectedTeamId(data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedTeamId) return;
    setNormalizedLoading(true);
    setNormalizedError(null);
    api.normalizedScores(selectedTeamId)
      .then(setNormalized)
      .catch((e) => setNormalizedError(e.message))
      .finally(() => setNormalizedLoading(false));
  }, [selectedTeamId]);

  function toggleDetails(key) {
    setOpenDetails((d) => ({ ...d, [key]: !d[key] }));
  }

  return (
    <div className="admin-bias-page">
      <header className="admin-bias-page__header">
        <button className="admin-bias-page__back" onClick={() => navigate("/admin/dashboard")}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Dashboard
        </button>
        <h1>Bias &amp; Fairness</h1>
      </header>

      <main className="admin-bias-page__main">
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <h2 className="admin-bias-page__section-title">All reviewers</h2>
          {biasLoading && <div className="admin-bias-page__status">Loading reviewer bias…</div>}
          {biasError && <div className="admin-bias-page__error" role="alert">{biasError}</div>}
          {!biasLoading && !biasError && <BiasCardGrid items={bias} openDetails={openDetails} toggleDetails={toggleDetails} prefix="all" />}
        </motion.section>

        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
          <h2 className="admin-bias-page__section-title">Flagged reviewers</h2>
          {flaggedLoading && <div className="admin-bias-page__status">Loading flagged reviewers…</div>}
          {!flaggedLoading && flagged.length === 0 && <div className="admin-bias-page__status">No reviewers currently flagged. Good news.</div>}
          {!flaggedLoading && flagged.length > 0 && <BiasCardGrid items={flagged} openDetails={openDetails} toggleDetails={toggleDetails} prefix="flagged" />}
        </motion.section>

        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
          <h2 className="admin-bias-page__section-title">Team score comparison</h2>
          <p className="admin-bias-page__status" style={{ paddingTop: 0 }}>
            Each judge's raw score for this team, side by side with the bias-corrected normalized score.
          </p>
          <select
            className="admin-bias-page__team-select"
            value={selectedTeamId || ""}
            onChange={(e) => setSelectedTeamId(Number(e.target.value))}
          >
            {teams.map((t) => (
              <option key={t.id} value={t.id}>{t.team_name}</option>
            ))}
          </select>

          {normalizedLoading && <div className="admin-bias-page__status">Loading scores…</div>}
          {normalizedError && <div className="admin-bias-page__error" role="alert">{normalizedError}</div>}
          {!normalizedLoading && !normalizedError && normalized.length === 0 && (
            <div className="admin-bias-page__status">No scores submitted for this team yet.</div>
          )}
          {!normalizedLoading && normalized.length > 0 && (
            <div className="admin-bias-page__norm-table">
              <div className="admin-bias-page__norm-row admin-bias-page__norm-row--head">
                <span>Judge</span>
                <span>Raw score</span>
                <span>Normalized score</span>
                <span>Why</span>
              </div>
              {normalized.map((entry) => (
                <div key={entry.score_id} className="admin-bias-page__norm-row">
                  <span className="admin-bias-page__norm-name">{entry.reviewer_name}</span>
                  <span className="admin-bias-page__norm-raw">{entry.raw_score}</span>
                  <span className="admin-bias-page__norm-score">{entry.normalized_score}</span>
                  <span className="admin-bias-page__norm-explanation">{entry.explanation}</span>
                </div>
              ))}
            </div>
          )}
        </motion.section>

        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }}>
          <h2 className="admin-bias-page__section-title">Audit log</h2>
          {auditLoading && <div className="admin-bias-page__status">Loading audit log…</div>}
          {!auditLoading && audit.length === 0 && <div className="admin-bias-page__status">No audit entries yet.</div>}
          {!auditLoading && audit.length > 0 && (
            <div className="admin-bias-page__audit-list">
              {audit.slice(0, 50).map((entry) => (
                <div key={entry.id} className="admin-bias-page__audit-row">
                  <span className="admin-bias-page__audit-time">{formatTime(entry.timestamp)}</span>
                  <span className="admin-bias-page__audit-reviewer">{entry.actor}</span>
                  <span className="admin-bias-page__audit-team">{teamNameById[entry.after?.team_id] || "—"}</span>
                  <span className="admin-bias-page__audit-score">{entry.after?.score ?? "—"}</span>
                  <span className="admin-bias-page__audit-action">{entry.action}</span>
                </div>
              ))}
            </div>
          )}
        </motion.section>
      </main>
    </div>
  );
}

function BiasCardGrid({ items, openDetails, toggleDetails, prefix }) {
  if (items.length === 0) return <div className="admin-bias-page__status">No data available.</div>;
  return (
    <div className="admin-bias-page__grid">
      {items.map((item) => {
        const key = `${prefix}-${item.reviewer_id}`;
        const open = !!openDetails[key];
        return (
          <GlassCard tone="light" key={key} className="admin-bias-page__card">
            <div className="admin-bias-page__card-head">
              <span className="admin-bias-page__card-name">{item.reviewer_name}</span>
              <RiskBadge level={item.bias_risk_level} kind="bias" />
            </div>
            <p className="admin-bias-page__card-summary">{item.summary}</p>
            <button className="admin-bias-page__details-toggle" onClick={() => toggleDetails(key)}>
              {open ? "Hide" : "Show"} technical details
            </button>
            {open && (
              <div className="admin-bias-page__details">
                <span>z-score: <strong>{item.z_score}</strong></span>
                <span>mean score: <strong>{item.mean_score}</strong></span>
                <span>confidence: <strong>{item.confidence_label}</strong></span>
              </div>
            )}
          </GlassCard>
        );
      })}
    </div>
  );
}

function formatTime(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleString();
}
