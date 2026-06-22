import React, { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import NetworkField from "../components/NetworkField.jsx";
import GlassCard from "../components/GlassCard.jsx";
import BrandName from "../components/BrandName.jsx";
import Button from "../components/Button.jsx";
import { api } from "../api.js";
import { setSession } from "../auth.js";
import "./AdminLoginPage.css";

export default function AdminLoginPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "", organization_name: "" });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [showPassword, setShowPassword] = useState(false);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
    if (errors[field]) setErrors((e) => ({ ...e, [field]: null }));
  }

  function validate() {
    const next = {};
    if (mode === "signup" && !form.name.trim()) next.name = "Your name is required.";
    if (!form.email.trim()) next.email = "Email is required.";
    if (!form.password.trim()) next.password = "Password is required.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitError(null);
    if (!validate()) return;
    setSubmitting(true);
    try {
      const session =
        mode === "login"
          ? await api.organizerLogin({ email: form.email, password: form.password })
          : await api.organizerSignup(form);
      setSession(session);
      navigate("/admin/dashboard");
    } catch (err) {
      setSubmitError(err.message || "Could not sign you in.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="admin-login-page">
      <div className="admin-login-page__network">
        <NetworkField density={22} variant="ambient" />
      </div>

      <div className="admin-login-page__inner">
        <motion.div
          className="admin-login-page__brand"
          initial={{ opacity: 0, x: -24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.7 }}
        >
          <button className="admin-login-page__back" onClick={() => navigate("/")}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Back
          </button>

          <div className="admin-login-page__brand-name"><BrandName size="sm" /></div>

          <h1 className="admin-login-page__headline">
            Organizer<br />
            <span className="admin-login-page__accent">Command Center</span>
          </h1>

          <p className="admin-login-page__subhead">
            Sign in to create hackathons, manage participants, and track your event lifecycle end to end.
          </p>

          <div className="admin-login-page__features">
            <FeaturePill icon="🚀" text="Create & publish hackathons" />
            <FeaturePill icon="👥" text="Manage registrations" />
            <FeaturePill icon="⚖️" text="Automated reviewer matching" />
            <FeaturePill icon="🏆" text="Winner announcement tools" />
          </div>
        </motion.div>

        <div className="admin-login-page__form-panel">
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.15 }}>
            <GlassCard tone="light" className="admin-login-page__card">
              <div className="admin-login-page__card-header">
                <div className="admin-login-page__role-badge">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>
                  </svg>
                  {mode === "login" ? "Admin Login" : "Admin Sign Up"}
                </div>
                <h2>{mode === "login" ? "Welcome back, Organizer" : "Create your organizer account"}</h2>
              </div>

              <form onSubmit={handleSubmit} className="admin-login-page__form" noValidate>
                {mode === "signup" && (
                  <div className="admin-field">
                    <label className="admin-field__label">Your name <span className="admin-field__req">*</span></label>
                    <input
                      className={`admin-field__input ${errors.name ? "admin-field__input--error" : ""}`}
                      type="text"
                      placeholder="Ada Lovelace"
                      value={form.name}
                      onChange={(e) => update("name", e.target.value)}
                    />
                    {errors.name && <span className="admin-field__error">{errors.name}</span>}
                  </div>
                )}

                <div className="admin-field">
                  <label className="admin-field__label">Email <span className="admin-field__req">*</span></label>
                  <input
                    className={`admin-field__input ${errors.email ? "admin-field__input--error" : ""}`}
                    type="email"
                    placeholder="organizer@event.dev"
                    value={form.email}
                    onChange={(e) => update("email", e.target.value)}
                    autoComplete="email"
                  />
                  {errors.email && <span className="admin-field__error">{errors.email}</span>}
                </div>

                {mode === "signup" && (
                  <div className="admin-field">
                    <label className="admin-field__label">Organization (optional)</label>
                    <input
                      className="admin-field__input"
                      type="text"
                      placeholder="e.g. IIT Jaipur Tech Fest"
                      value={form.organization_name}
                      onChange={(e) => update("organization_name", e.target.value)}
                    />
                  </div>
                )}

                <div className="admin-field">
                  <label className="admin-field__label">Password <span className="admin-field__req">*</span></label>
                  <div className="admin-field__password-wrap">
                    <input
                      className={`admin-field__input admin-field__input--password ${errors.password ? "admin-field__input--error" : ""}`}
                      type={showPassword ? "text" : "password"}
                      placeholder="••••••••"
                      value={form.password}
                      onChange={(e) => update("password", e.target.value)}
                      autoComplete="current-password"
                    />
                    <button type="button" className="admin-field__eye" onClick={() => setShowPassword((s) => !s)}>
                      {showPassword ? (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19M1 1l22 22" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
                      ) : (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" strokeWidth="1.8"/><circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8"/></svg>
                      )}
                    </button>
                  </div>
                  {errors.password && <span className="admin-field__error">{errors.password}</span>}
                </div>

                {submitError && <div className="admin-login-page__submit-error">{submitError}</div>}

                <Button type="submit" variant="primary" size="lg" loading={submitting} className="admin-login-page__submit">
                  {submitting ? "Please wait…" : mode === "login" ? "Sign in to Dashboard" : "Create account"}
                </Button>

                <p className="admin-login-page__fineprint">
                  {mode === "login" ? "Need an organizer account? " : "Already have one? "}
                  <button
                    type="button"
                    style={{ background: "none", border: "none", color: "inherit", textDecoration: "underline", cursor: "pointer", padding: 0 }}
                    onClick={() => setMode(mode === "login" ? "signup" : "login")}
                  >
                    {mode === "login" ? "Sign up" : "Log in"}
                  </button>
                </p>
              </form>
            </GlassCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function FeaturePill({ icon, text }) {
  return (
    <div className="admin-feature-pill">
      <span>{icon}</span>
      <span>{text}</span>
    </div>
  );
}
