import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate, useParams } from "react-router-dom";

import GlassCard from "../components/GlassCard.jsx";
import Button from "../components/Button.jsx";
import { TextAreaField } from "../components/Field.jsx";
import { api } from "../api.js";
import "./ReviewerScorePage.css";

export default function ReviewerScorePage() {
  const navigate = useNavigate();
  const { teamId } = useParams();
  const [me, setMe] = useState(null);
  const [assignment, setAssignment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [score, setScore] = useState("");
  const [innovation, setInnovation] = useState("");
  const [technical, setTechnical] = useState("");
  const [presentation, setPresentation] = useState("");
  const [comments, setComments] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const myProfile = await api.getMe();
        setMe(myProfile);
        const list = await api.listAssignments();
        setAssignment(list.find((a) => String(a.team_id) === String(teamId)) || null);
      } catch (err) {
        setError(err.message || "Could not load team details.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [teamId]);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitError(null);
    if (score === "" || innovation === "" || technical === "" || presentation === "") {
      setSubmitError("Please fill in the overall score and all three sub-scores.");
      return;
    }
    setSubmitting(true);
    try {
      await api.submitScore({
        reviewer_id: me.id,
        team_id: Number(teamId),
        score: Number(score),
        criteria: { innovation: Number(innovation), technical: Number(technical), presentation: Number(presentation) },
        comments,
      });
      setDone(true);
    } catch (err) {
      setSubmitError(err.message || "Could not submit score. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <div className="reviewer-score-page">
        <motion.div className="reviewer-score-page__success" initial={{ opacity: 0, scale: 0.94, y: 18 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="reviewer-score-page__success-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h2>Score submitted</h2>
          <p>Your evaluation for Team {teamId} has been recorded.</p>
          <Button variant="primary" onClick={() => navigate("/reviewer/dashboard")}>Back to dashboard</Button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="reviewer-score-page">
      <div className="reviewer-score-page__inner">
        <button className="reviewer-score-page__back" onClick={() => navigate("/reviewer/dashboard")}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Dashboard
        </button>

        {loading && <div className="reviewer-score-page__status">Loading team details…</div>}
        {error && <div className="reviewer-score-page__error" role="alert">{error}</div>}

        {!loading && (
          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <GlassCard tone="light" className="reviewer-score-page__card">
              <div className="reviewer-score-page__head">
                <span className="reviewer-score-page__eyebrow">Score this team</span>
                <h1>Team {teamId}</h1>
                {assignment?.explanation && <p className="reviewer-score-page__explanation">{assignment.explanation}</p>}
              </div>

              <form onSubmit={handleSubmit} className="reviewer-score-page__form">
                <label className="reviewer-score-page__field">
                  Overall score
                  <input type="number" className="reviewer-score-page__input" value={score} onChange={(e) => setScore(e.target.value)} min="0" max="100" placeholder="0–100" />
                </label>

                <div className="reviewer-score-page__row">
                  <label className="reviewer-score-page__field">
                    Innovation
                    <input type="number" className="reviewer-score-page__input" value={innovation} onChange={(e) => setInnovation(e.target.value)} min="0" max="10" />
                  </label>
                  <label className="reviewer-score-page__field">
                    Technical
                    <input type="number" className="reviewer-score-page__input" value={technical} onChange={(e) => setTechnical(e.target.value)} min="0" max="10" />
                  </label>
                  <label className="reviewer-score-page__field">
                    Presentation
                    <input type="number" className="reviewer-score-page__input" value={presentation} onChange={(e) => setPresentation(e.target.value)} min="0" max="10" />
                  </label>
                </div>

                <TextAreaField label="Comments" placeholder="Notes for the team or organizers…" rows={4} value={comments} onChange={(e) => setComments(e.target.value)} />

                {submitError && <div className="reviewer-score-page__error" role="alert">{submitError}</div>}

                <Button type="submit" variant="primary" size="lg" loading={submitting} className="reviewer-score-page__submit">
                  {submitting ? "Submitting…" : "Submit score"}
                </Button>
              </form>
            </GlassCard>
          </motion.div>
        )}
      </div>
    </div>
  );
}
