import React, { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import NetworkField from "../components/NetworkField.jsx";
import GlassCard from "../components/GlassCard.jsx";
import BrandName from "../components/BrandName.jsx";
import Button from "../components/Button.jsx";
import { TextField } from "../components/Field.jsx";
import { api } from "../api.js";
import { setSession } from "../auth.js";
import "./ReviewerLoginPage.css";

export default function ReviewerLoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [needsInvite, setNeedsInvite] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email.trim()) return;
    setSubmitting(true);
    setError(null);
    setNeedsInvite(false);
    try {
      const session = await api.judgeLogin(email.trim());
      setSession(session);
      navigate("/reviewer/dashboard");
    } catch (err) {
      if (err.message && err.message.includes("invite link")) {
        setNeedsInvite(true);
      } else {
        setError(err.message || "Could not log in.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="reviewer-login-page">
      <div className="reviewer-login-page__network">
        <NetworkField density={20} variant="ambient" />
      </div>

      <button className="reviewer-login-page__back" onClick={() => navigate("/")}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Back
      </button>

      <div className="reviewer-login-page__inner">
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <GlassCard tone="light" className="reviewer-login-page__card">
            <div className="reviewer-login-page__brand"><BrandName size="sm" /></div>

            <div className="reviewer-login-page__role-badge">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="4" width="18" height="17" rx="2" stroke="currentColor" strokeWidth="1.6"/>
              </svg>
              Reviewer / Judge
            </div>

            {needsInvite ? (
              <>
                <h2 className="reviewer-login-page__title">Don't have a link yet?</h2>
                <p className="reviewer-login-page__sub">
                  We couldn't find a judge account with that email. Judges join
                  through an invite link shared by the organizer — there's no
                  roster to pick from here. Ask your organizer to send you the
                  judge invite link for the event.
                </p>
                <Button variant="outline" size="md" onClick={() => setNeedsInvite(false)} style={{ marginBottom: 10 }}>
                  Try a different email
                </Button>
                <Button variant="primary" size="lg" className="reviewer-login-page__submit" onClick={() => navigate("/")}>
                  Back to home
                </Button>
              </>
            ) : (
              <>
                <h2 className="reviewer-login-page__title">Welcome back, Judge</h2>
                <p className="reviewer-login-page__sub">
                  Already registered via an invite link? Log in with the email
                  you used to join.
                </p>

                {error && <div className="reviewer-login-page__error" role="alert">{error}</div>}

                <form onSubmit={handleSubmit} className="reviewer-login-page__form">
                  <TextField label="Email address" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
                  <Button type="submit" variant="primary" size="lg" loading={submitting} disabled={!email.trim()} className="reviewer-login-page__submit">
                    {submitting ? "Logging in…" : "Log in"}
                  </Button>
                </form>

                <p className="reviewer-login-page__sub" style={{ marginTop: 14 }}>
                  No account yet? You'll need an invite link from your organizer — there's no self-registration for judges.
                </p>
              </>
            )}
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}
