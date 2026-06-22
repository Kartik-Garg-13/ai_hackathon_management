import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import GlassCard from "../components/GlassCard.jsx";
import Button from "../components/Button.jsx";
import { TextField, TagsField } from "../components/Field.jsx";
import { api, ensureHackathonSelected } from "../api.js";
import "./AdminReviewersPage.css";

const initialForm = {
  name: "", organization: "", industry: "", experience_years: "", max_load: "", expertise: [], role: "judge",
};

export default function AdminReviewersPage() {
  const navigate = useNavigate();
  const [reviewers, setReviewers] = useState([]);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState(null);

  const [form, setForm] = useState(initialForm);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState(null);

  const [assigning, setAssigning] = useState(false);
  const [assignError, setAssignError] = useState(null);
  const [assignments, setAssignments] = useState([]);

  async function loadReviewers() {
    setListLoading(true);
    setListError(null);
    try {
      setReviewers(await api.listReviewers());
    } catch (err) {
      setListError(err.message || "Could not load reviewers.");
    } finally {
      setListLoading(false);
    }
  }

  useEffect(() => {
    ensureHackathonSelected().then((ok) => {
      if (!ok) {
        setListError("No hackathon found for this account — create one from the dashboard first.");
        setListLoading(false);
        return;
      }
      loadReviewers();
      api.listAssignments().then(setAssignments).catch(() => {});
    });
  }, []);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleCreate(e) {
    e.preventDefault();
    setCreateError(null);
    if (!form.name.trim()) {
      setCreateError("Name is required.");
      return;
    }
    setCreating(true);
    try {
      await api.createReviewer({
        name: form.name,
        organization: form.organization,
        industry: form.industry,
        experience_years: form.experience_years ? Number(form.experience_years) : 0,
        max_load: form.max_load ? Number(form.max_load) : 5,
        expertise: form.expertise,
        role: form.role,
      });
      setForm(initialForm);
      await loadReviewers();
    } catch (err) {
      setCreateError(err.message || "Could not create reviewer.");
    } finally {
      setCreating(false);
    }
  }

  async function handleRunAssignment() {
    setAssigning(true);
    setAssignError(null);
    try {
      await api.runAssignment();
      setAssignments(await api.listAssignments());
    } catch (err) {
      setAssignError(err.message || "Could not run reviewer assignment.");
    } finally {
      setAssigning(false);
    }
  }

  function reviewerName(id) {
    const r = reviewers.find((rv) => String(rv.id) === String(id));
    return r ? r.name : `Reviewer ${id}`;
  }

  return (
    <div className="admin-rev-page">
      <header className="admin-rev-page__header">
        <button className="admin-rev-page__back" onClick={() => navigate("/admin/dashboard")}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Dashboard
        </button>
        <h1>Reviewers</h1>
      </header>

      <main className="admin-rev-page__main">
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <GlassCard tone="light" className="admin-rev-page__card">
            <h2>Roster</h2>
            {listLoading && <div className="admin-rev-page__status">Loading reviewers…</div>}
            {listError && <div className="admin-rev-page__error" role="alert">{listError}</div>}
            {!listLoading && !listError && reviewers.length === 0 && (
              <div className="admin-rev-page__status">No reviewers yet. Add one below, or share an invite link from the dashboard.</div>
            )}
            {!listLoading && !listError && reviewers.length > 0 && (
              <div className="admin-rev-page__grid">
                {reviewers.map((r) => (
                  <div key={r.id} className="admin-rev-page__rev-card">
                    <div className="admin-rev-page__rev-name">{r.name} <span style={{ fontSize: 11, opacity: 0.7 }}>({r.role})</span></div>
                    <div className="admin-rev-page__rev-org">{r.organization}{r.email ? ` · ${r.email}` : ""}</div>
                    <div className="admin-rev-page__rev-tags">
                      {(r.expertise || []).map((tag) => <span key={tag} className="admin-rev-page__tag">{tag}</span>)}
                    </div>
                    <div className="admin-rev-page__rev-load">Load: {r.current_load ?? 0} / {r.max_load ?? "—"}</div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </motion.section>

        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
          <GlassCard tone="light" className="admin-rev-page__card">
            <h2>Add reviewer</h2>
            <form onSubmit={handleCreate} className="admin-rev-page__form">
              <div className="admin-rev-page__row">
                <TextField label="Name" required value={form.name} onChange={(e) => update("name", e.target.value)} />
                <TextField label="Organization" value={form.organization} onChange={(e) => update("organization", e.target.value)} />
              </div>
              <div className="admin-rev-page__row">
                <label className="field">
                  <span className="field__label">Role</span>
                  <div className="field__control">
                    <select className="field__input" value={form.role} onChange={(e) => update("role", e.target.value)}>
                      <option value="judge">Judge</option>
                      <option value="mentor">Mentor</option>
                    </select>
                  </div>
                </label>
                <TextField label="Industry" value={form.industry} onChange={(e) => update("industry", e.target.value)} />
              </div>
              <div className="admin-rev-page__row">
                <TextField label="Experience (years)" type="number" value={form.experience_years} onChange={(e) => update("experience_years", e.target.value)} />
                <TextField label="Max load" type="number" value={form.max_load} onChange={(e) => update("max_load", e.target.value)} />
              </div>
              <TagsField label="Expertise" value={form.expertise} onChange={(tags) => update("expertise", tags)} placeholder="AI/ML, FinTech, Design…" />
              {createError && <div className="admin-rev-page__error" role="alert">{createError}</div>}
              <Button type="submit" variant="primary" loading={creating} className="admin-rev-page__submit">
                {creating ? "Adding…" : "Add reviewer"}
              </Button>
            </form>
          </GlassCard>
        </motion.section>

        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
          <GlassCard tone="light" className="admin-rev-page__card">
            <div className="admin-rev-page__assign-head">
              <h2>Reviewer assignment</h2>
              <Button variant="primary" size="sm" loading={assigning} onClick={handleRunAssignment}>
                {assigning ? "Running…" : "Run assignment"}
              </Button>
            </div>
            {assignError && <div className="admin-rev-page__error" role="alert">{assignError}</div>}
            {assignments.length > 0 && (
              <div className="admin-rev-page__assign-list">
                {assignments.map((a) => (
                  <div key={a.id} className="admin-rev-page__assign-row">
                    <span className="admin-rev-page__assign-team">Team {a.team_id}</span>
                    <span className="admin-rev-page__assign-reviewer">{reviewerName(a.reviewer_id)}</span>
                    {a.explanation && <span className="admin-rev-page__assign-explanation">{a.explanation}</span>}
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </motion.section>
      </main>
    </div>
  );
}
