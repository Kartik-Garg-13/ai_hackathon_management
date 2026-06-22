import React, { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import NetworkField from "../components/NetworkField.jsx";
import GlassCard from "../components/GlassCard.jsx";
import BrandName from "../components/BrandName.jsx";
import Button from "../components/Button.jsx";
import { api } from "../api.js";
import "./CreateHackathonPage.css";

const initialForm = {
  name: "",
  duration: "",
  teamSize: "",
  eligibility: "",
  mode: "online",
  problemStatements: "",
  prizes: "",
  registrationDeadline: "",
  eventDate: "",
  details: "",
  needsJudges: false,
  needsMentors: false,
};

export default function CreateHackathonPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [created, setCreated] = useState(null);
  const [links, setLinks] = useState(null);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
    if (errors[field]) setErrors((e) => ({ ...e, [field]: null }));
  }

  function validate() {
    const next = {};
    if (!form.name.trim()) next.name = "Hackathon name is required.";
    if (!form.duration.trim()) next.duration = "Duration is required.";
    if (!form.teamSize.trim()) next.teamSize = "Team size is required.";
    if (!form.eligibility.trim()) next.eligibility = "Eligibility criteria is required.";
    if (!form.details.trim()) next.details = "Event details are required.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitError(null);
    if (!validate()) return;
    setSubmitting(true);
    try {
      const description = [
        form.details,
        form.duration && `Duration: ${form.duration}`,
        form.teamSize && `Team size: ${form.teamSize}`,
        form.problemStatements && `Problem statements: ${form.problemStatements}`,
        form.prizes && `Prizes: ${form.prizes}`,
      ].filter(Boolean).join("\n\n");

      const hackathon = await api.createHackathon({
        name: form.name,
        description,
        eligibility_criteria: form.eligibility,
        mode: form.mode,
        registration_deadline: form.registrationDeadline ? new Date(form.registrationDeadline).toISOString() : null,
        start_date: form.eventDate ? new Date(form.eventDate).toISOString() : null,
        allow_judges: form.needsJudges,
        allow_mentors: form.needsMentors,
      });
      const generatedLinks = await api.generateInviteLinks(hackathon.id);
      setCreated(hackathon);
      setLinks(generatedLinks);
    } catch (err) {
      setSubmitError(err.message || "Could not create the hackathon. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  const joinUrl = (token) => `${window.location.origin}/join/${token}`;

  if (created) {
    return (
      <div className="create-hack__success-screen">
        <div className="create-hack__success-net">
          <NetworkField density={18} variant="ambient" />
        </div>
        <motion.div
          className="create-hack__success-card"
          initial={{ opacity: 0, scale: 0.92, y: 24 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <motion.div className="create-hack__success-icon" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 250, delay: 0.2 }}>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </motion.div>
          <h2 className="create-hack__success-title">Hackathon Created!</h2>
          <p className="create-hack__success-name">"{created.name}"</p>
          <p className="create-hack__success-desc">
            Share these invite links with judges, mentors, and participants.
          </p>
          <div style={{ textAlign: "left", margin: "16px 0", fontSize: 13 }}>
            {links?.map((link) => (
              <div key={link.id} style={{ marginBottom: 6 }}>
                <strong>{link.role}:</strong> <code>{joinUrl(link.token)}</code>{" "}
                <button
                  style={{ background: "none", border: "none", textDecoration: "underline", cursor: "pointer" }}
                  onClick={() => navigator.clipboard.writeText(joinUrl(link.token))}
                >
                  Copy
                </button>
              </div>
            ))}
          </div>
          <div className="create-hack__success-actions">
            <button className="create-hack__success-btn create-hack__success-btn--primary" onClick={() => navigate("/admin/dashboard")}>
              Back to Dashboard
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="create-hack-page">
      <div className="create-hack-page__net">
        <NetworkField density={16} variant="ambient" />
      </div>

      <header className="create-hack-page__header">
        <button className="create-hack-page__back" onClick={() => navigate("/admin/dashboard")}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Admin Dashboard
        </button>
        <div className="create-hack-page__brand"><BrandName size="sm" /></div>
      </header>

      <div className="create-hack-page__body">
        <motion.div className="create-hack-page__left" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6 }}>
          <div className="create-hack-page__eyebrow">New Hackathon</div>
          <h1 className="create-hack-page__title">Create your<br /><span className="create-hack-page__accent">event</span></h1>
          <p className="create-hack-page__sub">Fill in the details below. Once published, the event goes live with real invite links for judges, mentors, and participants.</p>

          <div className="create-hack-page__checklist">
            {["Event identity (name, date)", "Duration & team rules", "Eligibility criteria", "Problem statements", "Prizes & rewards", "Event description"].map((item, i) => (
              <div key={i} className="create-hack-page__check-item">
                <span className="create-hack-page__check-dot" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </motion.div>

        <div className="create-hack-page__right">
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }}>
            <GlassCard tone="light" className="create-hack-page__card">
              <form onSubmit={handleSubmit} className="create-hack-page__form" noValidate>
                <FormField label="Hackathon Name" required error={errors.name}>
                  <input className={`chf-input ${errors.name ? "chf-input--err" : ""}`} type="text" placeholder="e.g. CodeSprint 2026" value={form.name} onChange={(e) => update("name", e.target.value)} />
                </FormField>

                <div className="create-hack-page__row">
                  <FormField label="Duration" required error={errors.duration}>
                    <input className={`chf-input ${errors.duration ? "chf-input--err" : ""}`} type="text" placeholder="e.g. 36 hours" value={form.duration} onChange={(e) => update("duration", e.target.value)} />
                  </FormField>
                  <FormField label="Team Size" required error={errors.teamSize}>
                    <input className={`chf-input ${errors.teamSize ? "chf-input--err" : ""}`} type="text" placeholder="e.g. 2–4 members" value={form.teamSize} onChange={(e) => update("teamSize", e.target.value)} />
                  </FormField>
                </div>

                <div className="create-hack-page__row">
                  <FormField label="Registration Deadline">
                    <input className="chf-input" type="date" value={form.registrationDeadline} onChange={(e) => update("registrationDeadline", e.target.value)} />
                  </FormField>
                  <FormField label="Event Date">
                    <input className="chf-input" type="date" value={form.eventDate} onChange={(e) => update("eventDate", e.target.value)} />
                  </FormField>
                </div>

                <FormField label="Mode">
                  <div className="chf-radio-group">
                    {["online", "offline", "hybrid"].map((m) => (
                      <label key={m} className={`chf-radio ${form.mode === m ? "chf-radio--active" : ""}`}>
                        <input type="radio" name="mode" value={m} checked={form.mode === m} onChange={() => update("mode", m)} />
                        {m.charAt(0).toUpperCase() + m.slice(1)}
                      </label>
                    ))}
                  </div>
                </FormField>

                <FormField label="Eligibility Criteria" required error={errors.eligibility}>
                  <input className={`chf-input ${errors.eligibility ? "chf-input--err" : ""}`} type="text" placeholder="e.g. Open to all college students" value={form.eligibility} onChange={(e) => update("eligibility", e.target.value)} />
                </FormField>

                <FormField label="Problem Statements">
                  <textarea className="chf-input chf-textarea" rows={3} placeholder="List the problem statements or themes participants can choose from…" value={form.problemStatements} onChange={(e) => update("problemStatements", e.target.value)} />
                </FormField>

                <FormField label="Prizes & Rewards">
                  <input className="chf-input" type="text" placeholder="e.g. 1st: ₹50,000 | 2nd: ₹25,000 | 3rd: ₹10,000" value={form.prizes} onChange={(e) => update("prizes", e.target.value)} />
                </FormField>

                <FormField label="Event Details" required error={errors.details}>
                  <textarea className={`chf-input chf-textarea ${errors.details ? "chf-input--err" : ""}`} rows={4} placeholder="Describe the event — schedule, judging criteria, resources provided, mentors, sponsors, rules…" value={form.details} onChange={(e) => update("details", e.target.value)} />
                </FormField>

                <FormField label="Support needed for this event">
                  <div className="chf-checkbox-group">
                    <label className={`chf-checkbox ${form.needsJudges ? "chf-checkbox--active" : ""}`}>
                      <input type="checkbox" checked={form.needsJudges} onChange={(e) => update("needsJudges", e.target.checked)} />
                      <span className="chf-checkbox__box" />
                      <span className="chf-checkbox__text">
                        <strong>External judges</strong>
                        <small>Generates a judge invite link for this hackathon.</small>
                      </span>
                    </label>
                    <label className={`chf-checkbox ${form.needsMentors ? "chf-checkbox--active" : ""}`}>
                      <input type="checkbox" checked={form.needsMentors} onChange={(e) => update("needsMentors", e.target.checked)} />
                      <span className="chf-checkbox__box" />
                      <span className="chf-checkbox__text">
                        <strong>Mentors</strong>
                        <small>Generates a mentor invite link for this hackathon.</small>
                      </span>
                    </label>
                  </div>
                </FormField>

                {submitError && <div className="chf-error" role="alert">{submitError}</div>}

                <Button type="submit" variant="primary" size="lg" loading={submitting} className="create-hack-page__submit">
                  {submitting ? "Publishing…" : "Publish Hackathon"}
                </Button>
              </form>
            </GlassCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function FormField({ label, required, error, children }) {
  return (
    <div className="chf-field">
      <label className="chf-label">{label}{required && <span className="chf-req"> *</span>}</label>
      {children}
      {error && <span className="chf-error">{error}</span>}
    </div>
  );
}
