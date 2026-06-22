import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import NetworkField from "../components/NetworkField.jsx";
import BrandName from "../components/BrandName.jsx";
import HackathonCard from "../components/HackathonCard.jsx";
import { api } from "../api.js";
import { getSession, setSession, clearSession } from "../auth.js";
import "./AdminDashboardPage.css";

const PROBLEM_STATEMENTS = [
  { id: 1, tag: "AI / ML", title: "AI-Powered Waste Management", desc: "Build an intelligent system to classify and route waste for recycling using computer vision and edge AI." },
  { id: 2, tag: "HealthTech", title: "Rural Healthcare Assistant", desc: "Design an offline-capable diagnostic assistant for rural clinics with limited internet connectivity." },
  { id: 3, tag: "FinTech", title: "Micro-Credit for Farmers", desc: "Create a platform enabling farmers to access micro-loans using satellite imagery-based crop yield prediction." },
  { id: 4, tag: "EdTech", title: "Adaptive Learning Engine", desc: "Build an AI tutor that adapts difficulty in real time based on student performance and learning pace." },
  { id: 5, tag: "Climate", title: "Carbon Footprint Tracker", desc: "Develop a personal carbon tracker that gives actionable, locality-aware suggestions to reduce emissions." },
  { id: 6, tag: "Smart Cities", title: "Traffic Decongestion AI", desc: "Design a system that predicts traffic hotspots and reroutes vehicles using real-time sensor data." },
];

export default function AdminDashboardPage() {
  const navigate = useNavigate();
  const session = getSession();
  const [activeIdx, setActiveIdx] = useState(0);
  const [hackathons, setHackathons] = useState([]);
  const [error, setError] = useState(null);
  const [links, setLinks] = useState({});
  const [lifecycleBusy, setLifecycleBusy] = useState(false);

  useEffect(() => {
    api.listMyHackathons().then(async (data) => {
      setHackathons(data);
      const entries = await Promise.all(
        data.map((h) => api.listInviteLinks(h.id).then((l) => [h.id, l]).catch(() => [h.id, null]))
      );
      const existing = Object.fromEntries(entries.filter(([, l]) => l && l.length > 0));
      setLinks((prev) => ({ ...existing, ...prev }));
    }).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveIdx((i) => (i + 1) % PROBLEM_STATEMENTS.length);
    }, 3200);
    return () => clearInterval(timer);
  }, []);

  function handleLogout() {
    clearSession();
    navigate("/");
  }

  function handleManage(hackathon) {
    setSession({ ...session, hackathon_id: hackathon.id });
    navigate("/admin/registrations");
  }

  async function handleGenerateLinks(hackathon) {
    try {
      setError(null);
      const generated = await api.generateInviteLinks(hackathon.id);
      setLinks({ ...links, [hackathon.id]: generated });
    } catch (e) {
      setError(e.message);
    }
  }

  function patchHackathon(updated) {
    setHackathons((prev) => prev.map((h) => (h.id === updated.id ? updated : h)));
  }

  async function withLifecycleAction(action, confirmMessage) {
    if (confirmMessage && !window.confirm(confirmMessage)) return;
    setLifecycleBusy(true);
    setError(null);
    try {
      patchHackathon(await action());
    } catch (e) {
      setError(e.message);
    } finally {
      setLifecycleBusy(false);
    }
  }

  const handleStop = (h) => withLifecycleAction(
    () => api.stopHackathon(h.id),
    `Stop "${h.name}"? Participants won't be able to submit GitHub/demo links or pitch decks until you resume it.`
  );
  const handleResume = (h) => withLifecycleAction(() => api.resumeHackathon(h.id));
  const handleEnd = (h) => withLifecycleAction(
    () => api.endHackathon(h.id),
    `End "${h.name}" permanently? This can't be undone — participants will be locked out of submissions for good.`
  );

  const joinUrl = (token) => `${window.location.origin}/join/${token}`;
  const current = PROBLEM_STATEMENTS[activeIdx];

  return (
    <div className="admin-dash">
      <header className="admin-dash__header">
        <div className="admin-dash__header-net">
          <NetworkField density={12} variant="active" />
        </div>
        <div className="admin-dash__header-inner">
          <div className="admin-dash__brand"><BrandName size="sm" /></div>
          <div className="admin-dash__header-right">
            <div className="admin-dash__org-badge">{session?.name}</div>
            <button className="admin-dash__logout" onClick={handleLogout}>Log out</button>
          </div>
        </div>
      </header>

      <div className="admin-dash__body">
        <div className="admin-dash__left">
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6 }}>
            <div className="admin-dash__section-label">Popular Problem Statements</div>
            <h2 className="admin-dash__left-title">Inspire your participants with trending challenges</h2>
          </motion.div>

          <div className="admin-dash__ps-stage">
            <AnimatePresence mode="wait">
              <motion.div
                key={current.id}
                className="admin-dash__ps-card"
                initial={{ opacity: 0, y: 28, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.97 }}
                transition={{ duration: 0.5 }}
              >
                <span className="admin-dash__ps-tag">{current.tag}</span>
                <h3 className="admin-dash__ps-title">{current.title}</h3>
                <p className="admin-dash__ps-desc">{current.desc}</p>
              </motion.div>
            </AnimatePresence>

            <div className="admin-dash__ps-dots">
              {PROBLEM_STATEMENTS.map((_, i) => (
                <button key={i} className={`admin-dash__ps-dot ${i === activeIdx ? "admin-dash__ps-dot--active" : ""}`} onClick={() => setActiveIdx(i)} />
              ))}
            </div>
          </div>

          {error && <div className="admin-dash__org-badge" style={{ marginTop: 16 }}>{error}</div>}

          <h2 className="admin-dash__left-title" style={{ marginTop: 32 }}>Your hackathons</h2>
          {hackathons.length === 0 && <p className="admin-dash__ps-desc">No hackathons yet — create one to get started.</p>}
          {hackathons.map((h) => (
            <div key={h.id} style={{ marginBottom: 16 }}>
              <HackathonCard
                hackathon={h}
                onManage={handleManage}
                onGenerateLinks={handleGenerateLinks}
                onStop={handleStop}
                onResume={handleResume}
                onEnd={handleEnd}
                lifecycleBusy={lifecycleBusy}
              />
              {links[h.id] && (
                <ul style={{ marginTop: 8, fontSize: 13 }}>
                  {links[h.id].map((link) => (
                    <li key={link.id}>
                      <strong>{link.role}:</strong> <code>{joinUrl(link.token)}</code>{" "}
                      <button
                        style={{ background: "none", border: "none", textDecoration: "underline", cursor: "pointer" }}
                        onClick={() => navigator.clipboard.writeText(joinUrl(link.token))}
                      >
                        Copy
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>

        <div className="admin-dash__right">
          <motion.div className="admin-dash__cta-wrap" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6, delay: 0.15 }}>
            <div className="admin-dash__welcome">
              Welcome back, <span className="admin-dash__welcome-name">{session?.name}</span>
            </div>

            <div className="admin-dash__cta-card">
              <div className="admin-dash__cta-icon">
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2v20M2 12h20" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
                </svg>
              </div>
              <h3 className="admin-dash__cta-title">Launch a new hackathon</h3>
              <p className="admin-dash__cta-desc">
                Set up your event in minutes — define problem statements, team rules, eligibility, and go live.
              </p>
              <motion.button
                className="admin-dash__cta-btn"
                onClick={() => navigate("/admin/create-hackathon")}
                animate={{ boxShadow: ["0 0 0 0 rgba(126,200,227,0.4)", "0 0 0 16px rgba(126,200,227,0)", "0 0 0 0 rgba(126,200,227,0)"] }}
                transition={{ duration: 2.2, repeat: Infinity, ease: "easeOut" }}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2v20M2 12h20" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/>
                </svg>
                Create a Hackathon
              </motion.button>
            </div>

            <div className="admin-dash__quick-stats">
              <QuickStat value={hackathons.filter((h) => (h.status || "active") === "active").length} label="Active Hackathons" />
            </div>

            <div className="admin-dash__quick-links">
              <QuickLink label="Registrations" desc="Upload CSVs & review risk" onClick={() => navigate("/admin/registrations")} />
              <QuickLink label="Analytics" desc="Risk & fraud overview" onClick={() => navigate("/admin/analytics")} />
              <QuickLink label="Reviewers" desc="Roster & assignment" onClick={() => navigate("/admin/reviewers")} />
              <QuickLink label="Bias & Fairness" desc="Reviewer fairness + audit log" onClick={() => navigate("/admin/bias")} />
              <QuickLink label="Project Insights" desc="Similarity & plagiarism checks" onClick={() => navigate("/admin/insights")} />
            </div>
            {session?.hackathon_id && (
              <p className="admin-dash__welcome" style={{ marginTop: 12, fontSize: 13 }}>
                Currently managing hackathon #{session.hackathon_id}
              </p>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function QuickLink({ label, desc, onClick }) {
  return (
    <button className="admin-dash__quick-link" onClick={onClick}>
      <span className="admin-dash__quick-link-label">{label}</span>
      <span className="admin-dash__quick-link-desc">{desc}</span>
    </button>
  );
}

function QuickStat({ value, label }) {
  return (
    <div className="admin-quick-stat">
      <span className="admin-quick-stat__value">{value}</span>
      <span className="admin-quick-stat__label">{label}</span>
    </div>
  );
}
