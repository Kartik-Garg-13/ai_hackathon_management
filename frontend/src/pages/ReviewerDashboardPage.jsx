import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import NetworkField from "../components/NetworkField.jsx";
import BrandName from "../components/BrandName.jsx";
import GlassCard from "../components/GlassCard.jsx";
import Button from "../components/Button.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import { api } from "../api.js";
import { getSession, clearSession } from "../auth.js";
import "./ReviewerDashboardPage.css";

export default function ReviewerDashboardPage() {
  const navigate = useNavigate();
  const session = getSession();
  const [me, setMe] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [biasEntry, setBiasEntry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const myProfile = await api.getMe();
        setMe(myProfile);

        const [assignmentData, biasData] = await Promise.all([
          api.listAssignments(),
          api.biasReport().catch(() => []),
        ]);
        setAssignments(assignmentData.filter((a) => String(a.reviewer_id) === String(myProfile.id)));
        setBiasEntry(biasData.find((b) => String(b.reviewer_id) === String(myProfile.id)) || null);
      } catch (err) {
        setError(err.message || "Could not load your assignments.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function handleLogout() {
    clearSession();
    navigate("/");
  }

  const showBiasPanel = biasEntry && (biasEntry.bias_risk_level === "Medium" || biasEntry.bias_risk_level === "High");

  return (
    <div className="reviewer-dash">
      <header className="reviewer-dash__header">
        <div className="reviewer-dash__header-net"><NetworkField density={12} variant="active" /></div>
        <div className="reviewer-dash__header-inner">
          <div className="reviewer-dash__brand"><BrandName size="sm" /></div>
          <div className="reviewer-dash__header-right">
            <div className="reviewer-dash__name-badge">{session?.name}</div>
            <button className="reviewer-dash__logout" onClick={handleLogout}>Log out</button>
          </div>
        </div>
      </header>

      <main className="reviewer-dash__main">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <h1 className="reviewer-dash__title">Your assigned teams</h1>
          <p className="reviewer-dash__sub">Score each team you've been matched with. Scores feed directly into the final rankings.</p>
        </motion.div>

        {showBiasPanel && (
          <GlassCard tone="light" className="reviewer-dash__bias-panel">
            <div className="reviewer-dash__bias-head">
              <span className="reviewer-dash__bias-title">Fairness check</span>
              <RiskBadge level={biasEntry.bias_risk_level} kind="bias" />
            </div>
            <p className="reviewer-dash__bias-summary">{biasEntry.summary}</p>
          </GlassCard>
        )}

        {loading && <div className="reviewer-dash__status">Loading your assignments…</div>}
        {error && <div className="reviewer-dash__error" role="alert">{error}</div>}

        {!loading && !error && assignments.length === 0 && (
          <div className="reviewer-dash__empty">No teams have been assigned to you yet. Check back after the organizer runs assignment.</div>
        )}

        {!loading && !error && assignments.length > 0 && (
          <div className="reviewer-dash__grid">
            {assignments.map((a) => (
              <GlassCard key={a.id} tone="light" hoverLift className="reviewer-dash__card">
                <h3 className="reviewer-dash__card-title">Team {a.team_id}</h3>
                {a.explanation && <p className="reviewer-dash__card-explanation">{a.explanation}</p>}
                <Button variant="primary" size="sm" onClick={() => navigate(`/reviewer/score/${a.team_id}`)}>
                  Score this team
                </Button>
              </GlassCard>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
