import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import NetworkField from "../components/NetworkField.jsx";
import GlassCard from "../components/GlassCard.jsx";
import BrandName from "../components/BrandName.jsx";
import Button from "../components/Button.jsx";
import { TextField, TagsField, TextAreaField } from "../components/Field.jsx";
import { api } from "../api.js";
import { setSession } from "../auth.js";
import "./LoginPage.css";

const EMPTY_FORM = {
  name: "", email: "", phone_number: "", college: "", skills: [], project_idea: "",
  team_name: "", github_username: "", academic_year: "", dietary_restriction: "",
  emergency_contact: "", consent_accepted: false,
};

export default function LoginPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("register");
  const [hackathons, setHackathons] = useState(null);
  const [hackathonId, setHackathonId] = useState("");
  const [form, setForm] = useState(EMPTY_FORM);
  const [loginEmail, setLoginEmail] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setHackathons(null);
    setHackathonId("");
    const fetcher = mode === "login" ? api.listAllPublicHackathons() : api.listOpenHackathons();
    fetcher.then(setHackathons).catch(() => setHackathons([]));
  }, [mode]);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!hackathonId) return;
    setSubmitting(true);
    setError(null);
    try {
      const session = await api.registerParticipant(hackathonId, { ...form, skills: form.skills.join(",") });
      setSession(session);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Could not complete registration.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleLogin(e) {
    e.preventDefault();
    if (!hackathonId || !loginEmail.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const session = await api.loginParticipant(hackathonId, loginEmail.trim());
      setSession(session);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Could not find a registration with that email.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-page__brand">
        <button className="login-page__back" onClick={() => navigate("/")}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Back
        </button>

        <div className="login-page__network"><NetworkField density={26} variant="ambient" /></div>

        <div className="login-page__brand-content">
          <motion.div className="brand-mark" initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <BrandName size="sm" />
          </motion.div>

          <motion.h1
            className="login-page__headline"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
          >
            Every great team
            <br />
            starts as a single node.
          </motion.h1>

          <motion.p
            className="login-page__subhead"
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.22 }}
          >
            Pick any hackathon that's currently open for registration and join
            in — no invite link required for participants.
          </motion.p>
        </div>
      </div>

      <div className="login-page__form-panel">
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.15 }} className="login-page__form-wrap">
          <GlassCard tone="light" className="login-page__card">
            <div className="login-page__card-header">
              <span className="login-page__eyebrow">{mode === "login" ? "Participant login" : "Participant registration"}</span>
              <h2>{mode === "login" ? "Welcome back" : "Join a hackathon"}</h2>
            </div>

            <p className="login-page__no-hack-notice" style={{ marginBottom: 4 }}>
              {mode === "login" ? "Already registered? " : "First time here? "}
              <button
                type="button"
                style={{ background: "none", border: "none", color: "inherit", textDecoration: "underline", cursor: "pointer", padding: 0 }}
                onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }}
              >
                {mode === "login" ? "Register instead" : "Log in instead"}
              </button>
            </p>

            {hackathons === null ? (
              <p className="login-page__no-hack-notice">Loading hackathons&hellip;</p>
            ) : hackathons.length === 0 ? (
              <p className="login-page__no-hack-notice">
                {mode === "login" ? "No hackathons found." : "No hackathons are open for registration right now — check back soon."}
              </p>
            ) : mode === "login" ? (
              <>
                {error && <div className="login-page__submit-error" role="alert">{error}</div>}
                <form onSubmit={handleLogin} className="login-page__form" noValidate>
                  <label className="login-page__hack-select-label">
                    Hackathon
                    <select
                      className="login-page__hack-select"
                      value={hackathonId}
                      onChange={(e) => setHackathonId(e.target.value)}
                      required
                    >
                      <option value="" disabled>Choose a hackathon&hellip;</option>
                      {hackathons.map((h) => (
                        <option key={h.id} value={h.id}>{h.name}</option>
                      ))}
                    </select>
                  </label>
                  <TextField label="Email address" type="email" required value={loginEmail} onChange={(e) => setLoginEmail(e.target.value)} />
                  <Button type="submit" variant="primary" size="lg" loading={submitting} disabled={!hackathonId || !loginEmail.trim()} className="login-page__submit">
                    {submitting ? "Logging in…" : "Log in"}
                  </Button>
                </form>
              </>
            ) : (
              <>
                {error && <div className="login-page__submit-error" role="alert">{error}</div>}

                <form onSubmit={handleSubmit} className="login-page__form" noValidate>
                  <label className="login-page__hack-select-label">
                    Hackathon
                    <select
                      className="login-page__hack-select"
                      value={hackathonId}
                      onChange={(e) => setHackathonId(e.target.value)}
                      required
                    >
                      <option value="" disabled>Choose a hackathon&hellip;</option>
                      {hackathons.map((h) => (
                        <option key={h.id} value={h.id}>{h.name}</option>
                      ))}
                    </select>
                  </label>

                  {hackathonId && (
                    <>
                      <div className="login-page__row login-page__row--split">
                        <TextField label="Full name" required value={form.name} onChange={(e) => update("name", e.target.value)} />
                        <TextField label="Email address" type="email" required value={form.email} onChange={(e) => update("email", e.target.value)} />
                      </div>
                      <div className="login-page__row login-page__row--split">
                        <TextField label="Phone" value={form.phone_number} onChange={(e) => update("phone_number", e.target.value)} />
                        <TextField label="College / institution" value={form.college} onChange={(e) => update("college", e.target.value)} />
                      </div>
                      <div className="login-page__row login-page__row--split">
                        <TextField label="Team name" value={form.team_name} onChange={(e) => update("team_name", e.target.value)} />
                        <TagsField label="Skills" value={form.skills} onChange={(v) => update("skills", v)} placeholder="React, ML, Figma…" />
                      </div>
                      <TextAreaField label="Project idea" rows={2} value={form.project_idea} onChange={(e) => update("project_idea", e.target.value)} />
                      <div className="login-page__row login-page__row--split">
                        <TextField label="GitHub username" value={form.github_username} onChange={(e) => update("github_username", e.target.value)} />
                        <TextField label="Academic year" placeholder="e.g. 3rd Year" value={form.academic_year} onChange={(e) => update("academic_year", e.target.value)} />
                      </div>
                      <div className="login-page__row login-page__row--split">
                        <TextField label="Dietary restriction" value={form.dietary_restriction} onChange={(e) => update("dietary_restriction", e.target.value)} />
                        <TextField label="Emergency contact" value={form.emergency_contact} onChange={(e) => update("emergency_contact", e.target.value)} />
                      </div>
                      <label className="login-page__hack-select-label">
                        <input
                          type="checkbox"
                          checked={form.consent_accepted}
                          onChange={(e) => update("consent_accepted", e.target.checked)}
                          required
                          style={{ marginRight: 8 }}
                        />
                        I accept the code of conduct
                      </label>
                    </>
                  )}

                  <Button type="submit" variant="primary" size="lg" loading={submitting} disabled={!hackathonId} className="login-page__submit">
                    {submitting ? "Joining…" : "Join Hackathon"}
                  </Button>
                </form>
              </>
            )}
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}
