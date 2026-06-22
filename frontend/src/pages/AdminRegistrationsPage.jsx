import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import GlassCard from "../components/GlassCard.jsx";
import Button from "../components/Button.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import { api } from "../api.js";
import { getSession, setSession } from "../auth.js";
import "./AdminRegistrationsPage.css";

const REQUIRED_COLUMNS = ["id", "name", "email", "college", "skills", "project_idea", "team_name", "phone_number"];
const RISK_OPTIONS = ["", "High Risk", "Medium Risk", "Low Risk"];
const APPROVAL_OPTIONS = ["", "pending", "approved", "rejected"];

export default function AdminRegistrationsPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [riskFilter, setRiskFilter] = useState("");
  const [approvalFilter, setApprovalFilter] = useState("");
  const [nameSearch, setNameSearch] = useState("");
  const [nameSearchInput, setNameSearchInput] = useState("");
  const [rows, setRows] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [reanalyzing, setReanalyzing] = useState(false);

  const [selected, setSelected] = useState(null);

  async function ensureHackathonSelected() {
    const session = getSession();
    if (session?.hackathon_id) return true;
    const hackathons = await api.listMyHackathons();
    if (!hackathons.length) return false;
    setSession({ ...session, hackathon_id: hackathons[0].id });
    return true;
  }

  async function refresh() {
    setListLoading(true);
    setListError(null);
    try {
      const ok = await ensureHackathonSelected();
      if (!ok) {
        setListError("No hackathon found for this account — create one from the dashboard first.");
        return;
      }
      const [r, a] = await Promise.all([
        api.listRegistrations(riskFilter || undefined, approvalFilter || undefined, nameSearch || undefined),
        api.registrationAnalytics(),
      ]);
      setRows(r);
      setAnalytics(a);
    } catch (err) {
      setListError(err.message || "Could not load registrations.");
    } finally {
      setListLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [riskFilter, approvalFilter, nameSearch]);

  useEffect(() => {
    const timer = setTimeout(() => setNameSearch(nameSearchInput.trim()), 300);
    return () => clearTimeout(timer);
  }, [nameSearchInput]);

  function handleFileChosen(file) {
    setUploadError(null);
    setUploadResult(null);
    if (!file) return;
    doUpload(file);
  }

  async function doUpload(file) {
    setUploading(true);
    try {
      const result = await api.uploadRegistrations(file);
      setUploadResult(result);
      await refresh();
    } catch (err) {
      setUploadError(err.message || "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function handleReanalyze() {
    setReanalyzing(true);
    try {
      await api.reanalyzeRegistrations();
      await refresh();
    } catch (err) {
      setListError(err.message || "Could not re-analyze.");
    } finally {
      setReanalyzing(false);
    }
  }

  async function handleApprove(id) {
    await api.approveRegistration(id);
    setSelected(null);
    await refresh();
  }

  async function handleReject(id) {
    await api.rejectRegistration(id);
    setSelected(null);
    await refresh();
  }

  return (
    <div className="admin-reg-page">
      <header className="admin-reg-page__header">
        <button className="admin-reg-page__back" onClick={() => navigate("/admin/dashboard")}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Dashboard
        </button>
        <h1>Registrations</h1>
      </header>

      <main className="admin-reg-page__main">
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <GlassCard tone="light" className="admin-reg-page__upload-card">
            <h2>Upload a registrations CSV</h2>
            <p className="admin-reg-page__upload-hint">
              Required columns: {REQUIRED_COLUMNS.join(", ")} (ground_truth_label, ip_address, github_username, academic_year optional).
            </p>

            <div className="admin-reg-page__dropzone" onClick={() => fileInputRef.current?.click()}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path d="M12 16V4M12 4l-4 4M12 4l4 4M4 16v3a2 2 0 002 2h12a2 2 0 002-2v-3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>Click to browse, or drag a CSV here</span>
              <input ref={fileInputRef} type="file" accept=".csv,text/csv" className="admin-reg-page__file-input" onChange={(e) => handleFileChosen(e.target.files?.[0])} />
            </div>

            {uploading && <div className="admin-reg-page__status">Uploading & analyzing…</div>}
            {uploadError && <div className="admin-reg-page__error" role="alert">{uploadError}</div>}

            {uploadResult && (
              <div className="admin-reg-page__result-grid">
                <ResultStat label="Rows ingested" value={uploadResult.rows_ingested} />
                <ResultStat label="Teams created" value={uploadResult.teams_created} />
              </div>
            )}

            <div style={{ marginTop: 12 }}>
              <Button variant="outline" size="sm" loading={reanalyzing} onClick={handleReanalyze}>
                {reanalyzing ? "Re-analyzing…" : "Re-analyze All"}
              </Button>
              <span className="admin-reg-page__upload-hint" style={{ marginLeft: 10 }}>
                Best results with 20+ registrations — re-scores self-registered signups against the full population.
              </span>
            </div>
          </GlassCard>
        </motion.section>

        {analytics && (
          <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="admin-reg-page__result-grid">
              <ResultStat label="Total registrations" value={analytics.total_registrations} />
              <ResultStat label="Teams" value={analytics.total_teams} />
              <ResultStat label="High risk" value={analytics.high_risk_count} />
              <ResultStat label="Medium risk" value={analytics.medium_risk_count} />
              <ResultStat label="Low risk" value={analytics.low_risk_count} />
              <ResultStat label="Fraud rings" value={analytics.fraud_rings_detected} />
            </div>
          </motion.section>
        )}

        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
          <GlassCard tone="light" className="admin-reg-page__table-card">
            <div className="admin-reg-page__table-head">
              <h2>All registrations</h2>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  type="text"
                  className="admin-reg-page__filter"
                  placeholder="Search by name or team…"
                  value={nameSearchInput}
                  onChange={(e) => setNameSearchInput(e.target.value)}
                />
                <select className="admin-reg-page__filter" value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
                  {RISK_OPTIONS.map((opt) => <option key={opt} value={opt}>{opt || "All risk levels"}</option>)}
                </select>
                <select className="admin-reg-page__filter" value={approvalFilter} onChange={(e) => setApprovalFilter(e.target.value)}>
                  {APPROVAL_OPTIONS.map((opt) => <option key={opt} value={opt}>{opt || "All approval statuses"}</option>)}
                </select>
              </div>
            </div>

            {listLoading && <div className="admin-reg-page__status">Loading registrations…</div>}
            {listError && <div className="admin-reg-page__error" role="alert">{listError}</div>}

            {!listLoading && !listError && rows.length === 0 && (
              <div className="admin-reg-page__status">No registrations found for this filter.</div>
            )}

            {!listLoading && !listError && rows.length > 0 && (
              <div className="admin-reg-page__table">
                {rows.map((row) => (
                  <button key={row.id} className="admin-reg-page__row" onClick={() => setSelected(row)}>
                    <span className="admin-reg-page__row-name">
                      {row.name}
                      {row.team_name && <span className="admin-reg-page__row-team"> · {row.team_name}</span>}
                    </span>
                    {row.final_risk_level ? <RiskBadge level={row.final_risk_level} kind="registration" /> : <span className="admin-reg-page__row-explanation">Not yet analyzed</span>}
                    <span className="admin-reg-page__row-explanation">{row.approval_status}</span>
                  </button>
                ))}
              </div>
            )}
          </GlassCard>
        </motion.section>
      </main>

      {selected && (
        <div className="admin-reg-page__modal-backdrop" onClick={() => setSelected(null)}>
          <div className="admin-reg-page__modal" onClick={(e) => e.stopPropagation()}>
            <button className="admin-reg-page__modal-close" onClick={() => setSelected(null)}>×</button>
            <h2>{selected.name}{selected.team_name ? ` · ${selected.team_name}` : ""}</h2>
            {selected.final_risk_level && <RiskBadge level={selected.final_risk_level} kind="registration" />}
            <p className="admin-reg-page__modal-explanation">{selected.explanation}</p>
            {Array.isArray(selected.reasons) && selected.reasons.length > 0 && (
              <ul className="admin-reg-page__modal-reasons">
                {selected.reasons.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            )}
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <Button variant="primary" size="sm" onClick={() => handleApprove(selected.id)}>Approve</Button>
              <Button variant="outline" size="sm" onClick={() => handleReject(selected.id)}>Reject</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ResultStat({ label, value }) {
  return (
    <div className="admin-reg-page__stat">
      <span className="admin-reg-page__stat-value">{value}</span>
      <span className="admin-reg-page__stat-label">{label}</span>
    </div>
  );
}
