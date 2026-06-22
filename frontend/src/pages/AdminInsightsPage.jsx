import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import GlassCard from "../components/GlassCard.jsx";
import Button from "../components/Button.jsx";
import { api } from "../api.js";
import "./AdminInsightsPage.css";

export default function AdminInsightsPage() {
  const navigate = useNavigate();

  const [teams, setTeams] = useState([]);
  const [similarity, setSimilarity] = useState(null);
  const [similarityLoading, setSimilarityLoading] = useState(true);
  const [similarityError, setSimilarityError] = useState(null);

  const [scanResults, setScanResults] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState(null);

  useEffect(() => {
    api.listTeams().then(setTeams).catch(() => {});
    api.similarityReport().then(setSimilarity).catch((e) => setSimilarityError(e.message)).finally(() => setSimilarityLoading(false));
  }, []);

  function teamName(id) {
    return teams.find((t) => t.id === id)?.team_name || `Team #${id}`;
  }

  async function runScan() {
    setScanning(true);
    setScanError(null);
    try {
      setScanResults(await api.scanPlagiarism());
    } catch (e) {
      setScanError(e.message);
    } finally {
      setScanning(false);
    }
  }

  const teamsWithRepo = teams.filter((t) => t.github_repo_url);

  return (
    <div className="admin-insights-page">
      <header className="admin-insights-page__header">
        <button className="admin-insights-page__back" onClick={() => navigate("/admin/dashboard")}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Dashboard
        </button>
        <h1>Project Insights</h1>
      </header>

      <main className="admin-insights-page__main">
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <h2 className="admin-insights-page__section-title">Project categories</h2>
          {similarityLoading && <div className="admin-insights-page__status">Clustering project ideas&hellip;</div>}
          {similarityError && <div className="admin-insights-page__error" role="alert">{similarityError}</div>}
          {similarity && (
            <div className="admin-insights-page__category-grid">
              {similarity.categories.map((c) => (
                <GlassCard tone="light" key={c.label} className="admin-insights-page__category-card">
                  <span className="admin-insights-page__category-count">{c.team_count}</span>
                  <span className="admin-insights-page__category-label">{c.label}</span>
                </GlassCard>
              ))}
            </div>
          )}
        </motion.section>

        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
          <h2 className="admin-insights-page__section-title">Near-duplicate projects</h2>
          {similarity && similarity.duplicate_pairs.length === 0 && (
            <div className="admin-insights-page__status">No near-duplicate project ideas detected.</div>
          )}
          {similarity && similarity.duplicate_pairs.length > 0 && (
            <div className="admin-insights-page__pair-list">
              {similarity.duplicate_pairs.slice(0, 25).map((p, i) => (
                <div key={i} className="admin-insights-page__pair-row">
                  <span className="admin-insights-page__pair-teams">{p.team_a_name} <span className="admin-insights-page__pair-vs">vs</span> {p.team_b_name}</span>
                  <span className="admin-insights-page__pair-score">{Math.round(p.similarity * 100)}% similar</span>
                </div>
              ))}
            </div>
          )}
        </motion.section>

        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
          <h2 className="admin-insights-page__section-title">Live plagiarism scan</h2>
          <p className="admin-insights-page__hint">
            Compares the GitHub repos of the first {Math.min(teamsWithRepo.length, 10)} teams that have a repo
            link set ({teamsWithRepo.length} total have one). Uses real AST comparison for Python files and
            text-diff similarity for everything else — this calls the GitHub API live, so it can take a few
            seconds per team.
          </p>
          <Button variant="primary" size="md" loading={scanning} onClick={runScan} disabled={teamsWithRepo.length < 2}>
            {scanning ? "Scanning…" : "Run plagiarism scan"}
          </Button>
          {scanError && <div className="admin-insights-page__error" role="alert" style={{ marginTop: 10 }}>{scanError}</div>}
          {scanResults && scanResults.length === 0 && (
            <div className="admin-insights-page__status" style={{ marginTop: 10 }}>No medium/high-risk matches found.</div>
          )}
          {scanResults && scanResults.length > 0 && (
            <div className="admin-insights-page__pair-list" style={{ marginTop: 10 }}>
              {scanResults.map((r, i) => (
                <div key={i} className={`admin-insights-page__pair-row admin-insights-page__pair-row--${r.risk_level}`}>
                  <span className="admin-insights-page__pair-teams">{teamName(r.team_a_id)} <span className="admin-insights-page__pair-vs">vs</span> {teamName(r.team_b_id)}</span>
                  <span className="admin-insights-page__pair-score">{Math.round(r.overall_similarity * 100)}% similar &middot; {r.risk_level} risk</span>
                </div>
              ))}
            </div>
          )}
        </motion.section>
      </main>
    </div>
  );
}
