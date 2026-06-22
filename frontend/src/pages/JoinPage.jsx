import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate, useParams } from "react-router-dom";

import NetworkField from "../components/NetworkField.jsx";
import BrandName from "../components/BrandName.jsx";
import GlassCard from "../components/GlassCard.jsx";
import Button from "../components/Button.jsx";
import { TextField, TagsField, TextAreaField } from "../components/Field.jsx";
import { api } from "../api.js";
import { setSession } from "../auth.js";
import "./LoginPage.css";

const PARTICIPANT_FORM = {
  name: "", email: "", phone_number: "", college: "", skills: [], project_idea: "",
  team_name: "", github_username: "", academic_year: "", dietary_restriction: "",
  emergency_contact: "", consent_accepted: false,
};
const REVIEWER_FORM = {
  name: "", email: "", expertise: [], organization: "", industry: "",
  experience_years: "", linkedin_url: "", availability_window: "", bio: "", max_load: 5,
};

export default function JoinPage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [invite, setInvite] = useState(null);
  const [form, setForm] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api
      .resolveInvite(token)
      .then((info) => {
        setInvite(info);
        setForm(info.role === "participant" ? PARTICIPANT_FORM : REVIEWER_FORM);
      })
      .catch((e) => setError(e.message));
  }, [token]);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const session =
        invite.role === "participant"
          ? await api.registerParticipantViaInvite(token, { ...form, skills: form.skills.join(",") })
          : await api.registerReviewerViaInvite(token, {
              ...form,
              experience_years: Number(form.experience_years) || 0,
              max_load: Number(form.max_load) || 5,
            });
      setSession(session);
      if (session.role === "participant") navigate("/dashboard");
      else if (session.role === "judge") navigate("/reviewer/dashboard");
      else navigate("/mentor/dashboard");
    } catch (err) {
      setError(err.message || "Could not complete registration.");
    } finally {
      setSubmitting(false);
    }
  }

  if (error && !invite) {
    return (
      <div className="login-page">
        <div className="login-page__network"><NetworkField density={20} variant="ambient" /></div>
        <div className="login-page__form-panel">
          <GlassCard tone="light" className="login-page__card">
            <div className="login-page__card-header">
              <span className="login-page__eyebrow">Invite link</span>
              <h2>This link isn't valid</h2>
              <p>{error} — ask your organizer for a fresh invite link.</p>
            </div>
          </GlassCard>
        </div>
      </div>
    );
  }

  if (!invite) {
    return <div className="login-page" />;
  }

  return (
    <div className="login-page">
      <div className="login-page__brand">
        <div className="login-page__network"><NetworkField density={26} variant="ambient" /></div>
        <div className="login-page__brand-content">
          <div className="brand-mark"><BrandName size="sm" /></div>
          <motion.h1
            className="login-page__headline"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            {invite.hackathon_name}
          </motion.h1>
          <p className="login-page__subhead">
            You're joining as a <strong>{invite.role}</strong>. Fill in the details below to get started.
          </p>
        </div>
      </div>

      <div className="login-page__form-panel">
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="login-page__form-wrap">
          <GlassCard tone="light" className="login-page__card">
            <div className="login-page__card-header">
              <span className="login-page__eyebrow">{invite.role} registration</span>
              <h2>Join the hackathon</h2>
            </div>

            {error && <div className="login-page__submit-error" role="alert">{error}</div>}

            <form onSubmit={handleSubmit} className="login-page__form" noValidate>
              <div className="login-page__row login-page__row--split">
                <TextField label="Full name" required value={form.name} onChange={(e) => update("name", e.target.value)} />
                <TextField label="Email address" type="email" required value={form.email} onChange={(e) => update("email", e.target.value)} />
              </div>

              {invite.role === "participant" ? (
                <>
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
              ) : (
                <>
                  <TagsField label="Expertise" value={form.expertise} onChange={(v) => update("expertise", v)} placeholder="AI/ML, Backend, Design…" />
                  <div className="login-page__row login-page__row--split">
                    <TextField label="Organization" value={form.organization} onChange={(e) => update("organization", e.target.value)} />
                    <TextField label="Industry" value={form.industry} onChange={(e) => update("industry", e.target.value)} />
                  </div>
                  <div className="login-page__row login-page__row--split">
                    <TextField label="Years of experience" type="number" value={form.experience_years} onChange={(e) => update("experience_years", e.target.value)} />
                    <TextField label="Max teams you can review" type="number" value={form.max_load} onChange={(e) => update("max_load", e.target.value)} />
                  </div>
                  <div className="login-page__row login-page__row--split">
                    <TextField label="LinkedIn / portfolio" value={form.linkedin_url} onChange={(e) => update("linkedin_url", e.target.value)} />
                    <TextField label="Availability window" placeholder="e.g. Sat 10am-6pm" value={form.availability_window} onChange={(e) => update("availability_window", e.target.value)} />
                  </div>
                  <TextAreaField label="Short bio" rows={2} value={form.bio} onChange={(e) => update("bio", e.target.value)} />
                </>
              )}

              <Button type="submit" variant="primary" size="lg" loading={submitting} className="login-page__submit">
                {submitting ? "Joining…" : "Join Hackathon"}
              </Button>
            </form>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}
