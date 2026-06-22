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
import "./MentorLoginPage.css";

const EMPTY_FORM = {
  name: "", email: "", expertise: [], organization: "", industry: "",
  experience_years: "", linkedin_url: "", availability_window: "", bio: "", max_load: 5,
};

export default function MentorLoginPage() {
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
    fetcher
      .then((all) => setHackathons(all.filter((h) => h.allow_mentors)))
      .catch(() => setHackathons([]));
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
      const session = await api.registerMentor(hackathonId, {
        ...form,
        experience_years: Number(form.experience_years) || 0,
        max_load: Number(form.max_load) || 5,
      });
      setSession(session);
      navigate("/mentor/dashboard");
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
      const session = await api.loginReviewer(hackathonId, loginEmail.trim());
      setSession(session);
      navigate("/mentor/dashboard");
    } catch (err) {
      setError(err.message || "Could not find a registration with that email.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mentor-login-page">
      <div className="mentor-login-page__network">
        <NetworkField density={20} variant="ambient" />
      </div>

      <button className="mentor-login-page__back" onClick={() => navigate("/")}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Back
      </button>

      <div className="mentor-login-page__inner">
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <GlassCard tone="light" className="mentor-login-page__card">
            <div className="mentor-login-page__brand"><BrandName size="sm" /></div>

            <div className="mentor-login-page__role-badge">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="10" r="2.4" stroke="currentColor" strokeWidth="1.4"/>
              </svg>
              Mentor
            </div>

            <h2 className="mentor-login-page__title">{mode === "login" ? "Welcome back" : "Join a hackathon"}</h2>
            <p className="mentor-login-page__sub">
              {mode === "login"
                ? "Log back in to a hackathon you've already joined as a mentor."
                : "Pick any hackathon that's open for mentor registration — no invite link required."}
            </p>
            <p className="mentor-login-page__sub">
              {mode === "login" ? "First time here? " : "Already registered? "}
              <button
                type="button"
                style={{ background: "none", border: "none", color: "inherit", textDecoration: "underline", cursor: "pointer", padding: 0 }}
                onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }}
              >
                {mode === "login" ? "Register instead" : "Log in instead"}
              </button>
            </p>

            {hackathons === null ? (
              <p className="mentor-login-page__status">Loading hackathons&hellip;</p>
            ) : hackathons.length === 0 ? (
              <p className="mentor-login-page__status">
                {mode === "login" ? "No hackathons found." : "No hackathons are open for mentor registration right now — check back soon."}
              </p>
            ) : mode === "login" ? (
              <>
                {error && <div className="mentor-login-page__error" role="alert">{error}</div>}
                <form onSubmit={handleLogin} className="mentor-login-page__form" noValidate>
                  <label className="mentor-login-page__label">
                    Hackathon
                    <select
                      className="mentor-login-page__select"
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
                  <Button type="submit" variant="primary" size="lg" loading={submitting} disabled={!hackathonId || !loginEmail.trim()} className="mentor-login-page__submit">
                    {submitting ? "Logging in…" : "Log in"}
                  </Button>
                </form>
              </>
            ) : (
              <>
                {error && <div className="mentor-login-page__error" role="alert">{error}</div>}

                <form onSubmit={handleSubmit} className="mentor-login-page__form" noValidate>
                  <label className="mentor-login-page__label">
                    Hackathon
                    <select
                      className="mentor-login-page__select"
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
                      <TagsField label="Expertise" value={form.expertise} onChange={(v) => update("expertise", v)} placeholder="AI/ML, Backend, Design…" />
                      <div className="login-page__row login-page__row--split">
                        <TextField label="Organization" value={form.organization} onChange={(e) => update("organization", e.target.value)} />
                        <TextField label="Industry" value={form.industry} onChange={(e) => update("industry", e.target.value)} />
                      </div>
                      <div className="login-page__row login-page__row--split">
                        <TextField label="Years of experience" type="number" value={form.experience_years} onChange={(e) => update("experience_years", e.target.value)} />
                        <TextField label="Max teams you can mentor" type="number" value={form.max_load} onChange={(e) => update("max_load", e.target.value)} />
                      </div>
                      <div className="login-page__row login-page__row--split">
                        <TextField label="LinkedIn / portfolio" value={form.linkedin_url} onChange={(e) => update("linkedin_url", e.target.value)} />
                        <TextField label="Availability window" placeholder="e.g. Sat 10am-6pm" value={form.availability_window} onChange={(e) => update("availability_window", e.target.value)} />
                      </div>
                      <TextAreaField label="Short bio" rows={2} value={form.bio} onChange={(e) => update("bio", e.target.value)} />
                    </>
                  )}

                  <Button type="submit" variant="primary" size="lg" loading={submitting} disabled={!hackathonId} className="mentor-login-page__submit">
                    {submitting ? "Joining…" : "Join as Mentor"}
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
