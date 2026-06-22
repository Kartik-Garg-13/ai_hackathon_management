import React from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import NetworkField from "../components/NetworkField.jsx";
import BrandName from "../components/BrandName.jsx";
import BrainIntro from "../components/BrainIntro.jsx";
import "./LandingPage.css";

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <>
      <BrainIntro />
      <div className="landing-page">
      <div className="landing-page__network">
        <NetworkField density={28} variant="ambient" />
      </div>

      <motion.div
        className="landing-page__content"
        initial={{ opacity: 0, y: 36, scale: 0.97 }}
        whileInView={{ opacity: 1, y: 0, scale: 1 }}
        viewport={{ once: true, amount: 0.35 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="landing-page__brand">
          <BrandName size="md" />
        </div>

        <h1 className="landing-page__title">
          Power your hackathon.<br />
          <span className="landing-page__title-accent">Choose your role.</span>
        </h1>

        <p className="landing-page__sub">
          AI-validated registrations, automated reviewer matching, and bias-free judging — built for 24–48 hour events at any scale.
        </p>

        <div className="landing-page__cards">
          <motion.button
            className="landing-page__mode-card landing-page__mode-card--admin"
            onClick={() => navigate("/admin/login")}
            whileHover={{ scale: 1.025, y: -4 }}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.18, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="mode-card__icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
                <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="mode-card__body">
              <span className="mode-card__label">Organizer / Admin</span>
              <span className="mode-card__desc">Create and manage hackathons, track registrations, assign reviewers.</span>
            </div>
            <svg className="mode-card__arrow" width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </motion.button>

          <motion.button
            className="landing-page__mode-card landing-page__mode-card--participant"
            onClick={() => navigate("/participant/login")}
            whileHover={{ scale: 1.025, y: -4 }}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.28, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="mode-card__icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.6"/>
                <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
              </svg>
            </div>
            <div className="mode-card__body">
              <span className="mode-card__label">Participant</span>
              <span className="mode-card__desc">Register for hackathons, explore problem statements, track your submissions.</span>
            </div>
            <svg className="mode-card__arrow" width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </motion.button>

          <motion.button
            className="landing-page__mode-card landing-page__mode-card--reviewer"
            onClick={() => navigate("/reviewer/login")}
            whileHover={{ scale: 1.025, y: -4 }}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.38, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="mode-card__icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="4" width="18" height="17" rx="2" stroke="currentColor" strokeWidth="1.6"/>
                <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="mode-card__body">
              <span className="mode-card__label">Reviewer / Judge</span>
              <span className="mode-card__desc">Score assigned teams and review your own fairness metrics.</span>
            </div>
            <svg className="mode-card__arrow" width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </motion.button>

          <motion.button
            className="landing-page__mode-card landing-page__mode-card--mentor"
            onClick={() => navigate("/mentor/login")}
            whileHover={{ scale: 1.025, y: -4 }}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.48, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="mode-card__icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
                <circle cx="12" cy="10" r="2.4" stroke="currentColor" strokeWidth="1.4"/>
              </svg>
            </div>
            <div className="mode-card__body">
              <span className="mode-card__label">Mentor</span>
              <span className="mode-card__desc">Answer participant doubts in real time and help teams stay unblocked.</span>
            </div>
            <svg className="mode-card__arrow" width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </motion.button>
        </div>

        <div className="landing-page__stats">
          <Stat value="40%+" label="Less organizer workload" />
          <Stat value="100+" label="Participants per event" />
          <Stat value="0 bias" label="Reviewer assignment goal" />
        </div>
      </motion.div>
      </div>
    </>
  );
}

function Stat({ value, label }) {
  return (
    <div className="landing-stat">
      <span className="landing-stat__value">{value}</span>
      <span className="landing-stat__label">{label}</span>
    </div>
  );
}
