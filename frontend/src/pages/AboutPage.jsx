import React from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import NetworkField from "../components/NetworkField.jsx";
import BrandName from "../components/BrandName.jsx";
import GlassCard from "../components/GlassCard.jsx";
import "./AboutPage.css";

const TEAM = ["Kartik Garg"];

export default function AboutPage() {
  const navigate = useNavigate();

  return (
    <div className="about-page">
      <div className="about-page__network">
        <NetworkField density={22} variant="ambient" />
      </div>

      <button className="about-page__back" onClick={() => navigate("/")}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Back
      </button>

      <motion.div
        className="about-page__content"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
      >
        <div className="about-page__brand"><BrandName size="md" /></div>

        <h1 className="about-page__title">About us</h1>

        <GlassCard tone="light" className="about-page__card">
          <p>
            We're four students at Manipal University Jaipur, and this started as our
            entry for the Dell Futureminds AI Hackathon. We set out to build a hackathon
            management platform — the kind of tool that's usually a tangle of spreadsheets,
            forms, and someone's group chat falling apart at 3am.
          </p>
          <p>
            Somewhere along the way it stopped feeling like a submission. Eleven real
            features — fraud detection, bias-corrected judging, live plagiarism scanning,
            mentor matching, burnout tracking — and not a single one calls an LLM. Every
            "AI" decision here is something you can actually explain: a z-score, a cosine
            similarity, a decision tree, code you can read top to bottom. We built it that
            way on purpose — cheap to run, deterministic, and honest about what it's doing.
          </p>
          <p>
            We didn't expect to end up this proud of a hackathon project. It got good
            enough that we wanted more than a judging panel to see it — we wanted to put
            it out where anyone could try it. So here it is.
          </p>
        </GlassCard>

        <div className="about-page__team-grid">
          {TEAM.map((name) => (
            <div key={name} className="about-page__team-card">
              <span className="about-page__team-name">{name}</span>
              <span className="about-page__team-school">Manipal University Jaipur</span>
            </div>
          ))}
          <div className="about-page__team-card about-page__team-card--more">
            <span className="about-page__team-name">+ 3 teammates</span>
            <span className="about-page__team-school">Manipal University Jaipur</span>
          </div>
        </div>

        <p className="about-page__footer-note">
          Built for the Dell Futureminds AI Hackathon — DELLigent Minds.
        </p>
      </motion.div>
    </div>
  );
}
