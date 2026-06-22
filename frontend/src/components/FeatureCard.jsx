import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import GlassCard from "./GlassCard.jsx";
import { api } from "../api.js";
import "./FeatureCard.css";

export default function FeatureCard({ feature }) {
  const [running, setRunning] = useState(false);
  const [winners, setWinners] = useState(null);
  const [winnersError, setWinnersError] = useState(null);

  function handleRun() {
    setRunning(true);
    if (feature.id === "winner") {
      api.getWinners()
        .then(setWinners)
        .catch((e) => setWinnersError(e.message || "Could not check winner status."));
    }
    setTimeout(() => setRunning(false), 2600);
  }

  return (
    <GlassCard tone="light" hoverLift className="feature-card">
      <div className="feature-card__top">
        <span className={`feature-card__icon feature-card__icon--${feature.accent}`}>
          {feature.icon}
        </span>
        <span className="feature-card__status">{feature.status}</span>
      </div>

      <h3 className="feature-card__title">{feature.title}</h3>
      <p className="feature-card__desc">{feature.description}</p>

      <div className="feature-card__stage">
        {feature.id === "winner" && winners ? (
          <WinnerResult winners={winners} error={winnersError} />
        ) : (
          <FeatureAnimation type={feature.id} running={running} />
        )}
      </div>

      <button className="feature-card__cta" onClick={handleRun} disabled={running}>
        {running ? "Running…" : feature.cta}
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
    </GlassCard>
  );
}

function FeatureAnimation({ type, running }) {
  switch (type) {
    case "registration":
      return <RegistrationAnim running={running} />;
    case "reviewer":
      return <ReviewerAnim running={running} />;
    case "bias":
      return <BiasAnim running={running} />;
    case "winner":
      return <WinnerAnim running={running} />;
    default:
      return null;
  }
}

function RegistrationAnim({ running }) {
  const fields = ["ID", "Name", "Email", "College"];
  return (
    <div className="anim anim--registration">
      {fields.map((f, i) => (
        <div className="anim-row" key={f}>
          <span className="anim-row__label">{f}</span>
          <span className="anim-row__track">
            <motion.span
              className="anim-row__fill"
              initial={{ width: "0%" }}
              animate={{ width: running ? "100%" : "30%" }}
              transition={{ duration: 0.5, delay: running ? i * 0.22 : 0, ease: "easeOut" }}
            />
          </span>
          <AnimatePresence>
            {running && (
              <motion.span
                className="anim-row__check"
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0, opacity: 0 }}
                transition={{ delay: i * 0.22 + 0.4, duration: 0.25 }}
              >
                ✓
              </motion.span>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  );
}

function ReviewerAnim({ running }) {
  const entries = ["P1", "P2", "P3", "P4"];
  const reviewers = ["R-A", "R-B"];
  return (
    <div className="anim anim--reviewer">
      <div className="anim-reviewer__col">
        {entries.map((e, i) => (
          <motion.span
            className="anim-chip anim-chip--entry"
            key={e}
            animate={
              running
                ? { x: [0, 60, 60], opacity: [1, 1, 0] }
                : { x: 0, opacity: 1 }
            }
            transition={{ duration: 1.1, delay: i * 0.15, times: [0, 0.6, 1] }}
          >
            {e}
          </motion.span>
        ))}
      </div>
      <div className="anim-reviewer__arrow">
        <svg width="28" height="16" viewBox="0 0 28 16" fill="none">
          <path d="M0 8h24M18 1l7 7-7 7" stroke="#5b9bd1" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <div className="anim-reviewer__col">
        {reviewers.map((r, i) => (
          <motion.span
            className="anim-chip anim-chip--reviewer"
            key={r}
            animate={running ? { scale: [1, 1.12, 1] } : { scale: 1 }}
            transition={{ duration: 0.5, delay: 0.7 + i * 0.3 }}
          >
            {r}
          </motion.span>
        ))}
      </div>
    </div>
  );
}

function BiasAnim({ running }) {
  return (
    <div className="anim anim--bias">
      <div className="anim-bias__panel">
        {[...Array(6)].map((_, i) => (
          <span className="anim-bias__cell" key={i} />
        ))}
        {running && (
          <motion.div
            className="anim-bias__sweep"
            initial={{ left: "-30%" }}
            animate={{ left: "110%" }}
            transition={{ duration: 1.4, ease: "easeInOut" }}
          />
        )}
      </div>
      <motion.div
        className="anim-bias__verdict"
        initial={{ opacity: 0 }}
        animate={{ opacity: running ? 1 : 0 }}
        transition={{ delay: 1.5, duration: 0.4 }}
      >
        <span className="anim-bias__dot" /> Balanced — no skew detected
      </motion.div>
    </div>
  );
}

function WinnerResult({ winners, error }) {
  if (error) {
    return <p className="anim-bias__verdict" style={{ opacity: 1 }}>{error}</p>;
  }
  if (!winners.revealed) {
    return (
      <p className="anim-bias__verdict" style={{ opacity: 1 }}>
        The organizer hasn't revealed final results yet — check back later.
      </p>
    );
  }
  if (winners.rankings.length === 0) {
    return <p className="anim-bias__verdict" style={{ opacity: 1 }}>No scores have been submitted yet.</p>;
  }
  return (
    <div className="anim anim--winner">
      <div className="anim-podium">
        {winners.rankings.slice(0, 3).map((r) => (
          <div
            key={r.team_id}
            className="anim-podium__bar"
            style={{ height: `${Math.max(20, 60 - (r.rank - 1) * 16)}px` }}
          >
            <span className="anim-podium__place">{r.rank}</span>
          </div>
        ))}
      </div>
      <div className="anim-bias__verdict" style={{ opacity: 1, marginTop: 8 }}>
        {winners.rankings.slice(0, 3).map((r) => `#${r.rank} ${r.team_name}`).join(" · ")}
      </div>
    </div>
  );
}

function WinnerAnim({ running }) {
  return (
    <div className="anim anim--winner">
      <div className="anim-podium">
        {[
          { place: 2, h: 38, label: "Team Nimbus" },
          { place: 1, h: 54, label: "Team Vertex" },
          { place: 3, h: 28, label: "Team Aurora" },
        ].map((p, i) => (
          <motion.div
            className="anim-podium__bar"
            key={p.place}
            initial={{ height: 0 }}
            animate={{ height: running ? p.h : p.h * 0.5 }}
            transition={{ duration: 0.6, delay: running ? i * 0.15 : 0, ease: "backOut" }}
          >
            <span className="anim-podium__place">{p.place}</span>
          </motion.div>
        ))}
      </div>
      <AnimatePresence>
        {running && (
          <motion.div
            className="anim-confetti"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {[...Array(14)].map((_, i) => (
              <motion.span
                key={i}
                className="anim-confetti__piece"
                style={{
                  left: `${5 + Math.random() * 90}%`,
                  background: ["#4682b4", "#b0e0e6", "#f0f8ff"][i % 3],
                }}
                initial={{ y: -10, opacity: 0, rotate: 0 }}
                animate={{ y: 90, opacity: [0, 1, 0], rotate: 240 }}
                transition={{ duration: 1.3, delay: 0.3 + Math.random() * 0.4, ease: "easeIn" }}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
