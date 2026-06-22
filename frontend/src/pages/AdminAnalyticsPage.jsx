import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import GlassCard from "../components/GlassCard.jsx";
import Button from "../components/Button.jsx";
import { api, ensureHackathonSelected } from "../api.js";
import "./AdminAnalyticsPage.css";

const RISK_COLORS = {
  "Low Risk": "var(--c-success)",
  "Medium Risk": "var(--c-warning)",
  "High Risk": "var(--c-danger)",
};

export default function AdminAnalyticsPage() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [winners, setWinners] = useState(null);
  const [revealing, setRevealing] = useState(false);
  const [revealError, setRevealError] = useState(null);

  useEffect(() => {
    ensureHackathonSelected().then((ok) => {
      if (!ok) {
        setError("No hackathon found for this account — create one from the dashboard first.");
        setLoading(false);
        return;
      }
      Promise.all([api.registrationAnalytics(), api.judgeDashboard()])
        .then(([a, d]) => {
          setData(a);
          setDashboard(d);
        })
        .catch((err) => setError(err.message || "Could not load analytics."))
        .finally(() => setLoading(false));
      api.getWinners().then(setWinners).catch(() => {});
    });
  }, []);

  async function handleReveal() {
    setRevealing(true);
    setRevealError(null);
    try {
      setWinners(await api.revealWinners());
    } catch (err) {
      setRevealError(err.message || "Could not reveal winners.");
    } finally {
      setRevealing(false);
    }
  }

  const riskCounts = data
    ? { "Low Risk": data.low_risk_count, "Medium Risk": data.medium_risk_count, "High Risk": data.high_risk_count }
    : {};
  const maxCount = Math.max(1, ...Object.values(riskCounts));

  return (
    <div className="admin-analytics-page">
      <header className="admin-analytics-page__header">
        <button className="admin-analytics-page__back" onClick={() => navigate("/admin/dashboard")}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Dashboard
        </button>
        <h1>Analytics</h1>
      </header>

      <main className="admin-analytics-page__main">
        {loading && <div className="admin-analytics-page__status">Loading analytics…</div>}
        {error && <div className="admin-analytics-page__error" role="alert">{error}</div>}

        {!loading && !error && data && (
          <>
            <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
              <GlassCard tone="light" className="admin-analytics-page__card">
                <h2>Risk level distribution</h2>
                <div className="admin-analytics-page__bars">
                  {Object.entries(riskCounts).map(([key, value]) => {
                    const pct = Math.round((value / maxCount) * 100);
                    return (
                      <div key={key} className="admin-analytics-page__bar-row">
                        <span className="admin-analytics-page__bar-label">{key}</span>
                        <div className="admin-analytics-page__bar-track">
                          <div className="admin-analytics-page__bar-fill" style={{ width: `${pct}%`, background: RISK_COLORS[key] }} />
                        </div>
                        <span className="admin-analytics-page__bar-value">{value}</span>
                      </div>
                    );
                  })}
                </div>
              </GlassCard>
            </motion.section>

            <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
              <div className="admin-analytics-page__stat-grid">
                <GlassCard tone="light" className="admin-analytics-page__stat-card">
                  <span className="admin-analytics-page__stat-value">{data.total_registrations ?? "—"}</span>
                  <span className="admin-analytics-page__stat-label">Total registrations</span>
                </GlassCard>
                <GlassCard tone="light" className="admin-analytics-page__stat-card">
                  <span className="admin-analytics-page__stat-value">{data.total_teams ?? "—"}</span>
                  <span className="admin-analytics-page__stat-label">Teams</span>
                </GlassCard>
                <GlassCard tone="light" className="admin-analytics-page__stat-card">
                  <span className="admin-analytics-page__stat-value">{data.fraud_rings_detected ?? "—"}</span>
                  <span className="admin-analytics-page__stat-label">Fraud rings detected</span>
                </GlassCard>
              </div>
            </motion.section>

            {dashboard && (
              <>
                <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.15 }}>
                  <div className="admin-analytics-page__stat-grid">
                    <GlassCard tone="light" className="admin-analytics-page__stat-card">
                      <span className="admin-analytics-page__stat-value">{dashboard.active_team_count}</span>
                      <span className="admin-analytics-page__stat-label">Active teams</span>
                    </GlassCard>
                    <GlassCard tone="light" className="admin-analytics-page__stat-card">
                      <span className="admin-analytics-page__stat-value">{dashboard.inactive_team_count}</span>
                      <span className="admin-analytics-page__stat-label">Inactive teams</span>
                    </GlassCard>
                  </div>
                </motion.section>

                <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
                  <GlassCard tone="light" className="admin-analytics-page__card">
                    <h2>Project topics</h2>
                    {dashboard.category_distribution.map((c) => (
                      <div key={c.category} className="admin-analytics-page__bar-row">
                        <span className="admin-analytics-page__bar-label">{c.category}</span>
                        <span className="admin-analytics-page__bar-value">{c.team_count}</span>
                      </div>
                    ))}
                  </GlassCard>
                </motion.section>

                <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.25 }}>
                  <GlassCard tone="light" className="admin-analytics-page__card">
                    <h2>Top performing teams</h2>
                    {dashboard.top_teams.map((t, i) => (
                      <div key={t.team_id} className="admin-analytics-page__bar-row">
                        <span className="admin-analytics-page__bar-label">#{i + 1} {t.team_name}</span>
                        <span className="admin-analytics-page__bar-value">{t.average_normalized_score}/100</span>
                      </div>
                    ))}
                  </GlassCard>
                </motion.section>
              </>
            )}

            <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }}>
              <GlassCard tone="light" className="admin-analytics-page__card">
                <h2>Winner announcement</h2>
                {winners?.revealed ? (
                  <>
                    <p style={{ marginBottom: 10 }}>
                      Revealed to all participants at {new Date(winners.revealed_at).toLocaleString()}.
                    </p>
                    {winners.rankings.map((r) => (
                      <div key={r.team_id} className="admin-analytics-page__bar-row">
                        <span className="admin-analytics-page__bar-label">#{r.rank} {r.team_name}</span>
                        <span className="admin-analytics-page__bar-value">{r.average_normalized_score}/100</span>
                      </div>
                    ))}
                  </>
                ) : (
                  <>
                    <p style={{ marginBottom: 10 }}>
                      Final rankings are hidden from participants until you reveal them. This is permanent for this hackathon.
                    </p>
                    {revealError && <div className="admin-analytics-page__error" role="alert">{revealError}</div>}
                    <Button variant="primary" size="md" loading={revealing} onClick={handleReveal}>
                      Reveal winners to everyone
                    </Button>
                  </>
                )}
              </GlassCard>
            </motion.section>
          </>
        )}
      </main>
    </div>
  );
}
