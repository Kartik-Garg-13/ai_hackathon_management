import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./ProfileMenu.css";

export default function ProfileMenu({ participant, onLogout }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const initials = (participant?.name || "?")
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div className="profile-menu" ref={ref}>
      <button
        className="profile-menu__trigger"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="true"
        aria-expanded={open}
      >
        <span className="profile-menu__avatar">{initials}</span>
        <span className="profile-menu__name-wrap">
          <span className="profile-menu__name">{participant?.name || "Guest"}</span>
          <span className="profile-menu__id">{participant?.id || "—"}</span>
        </span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className={`profile-menu__chevron ${open ? "profile-menu__chevron--open" : ""}`}>
          <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            className="profile-menu__panel"
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="profile-menu__header">
              <span className="profile-menu__avatar profile-menu__avatar--lg">{initials}</span>
              <div>
                <div className="profile-menu__panel-name">{participant?.name || "Guest"}</div>
                <div className="profile-menu__panel-email">{participant?.email || "—"}</div>
              </div>
            </div>

            <div className="profile-menu__details">
              <DetailRow label="College" value={participant?.college} />
              <DetailRow label="Location" value={participant?.location} />
              <DetailRow
                label="Skills"
                value={participant?.skills?.length ? participant.skills.join(", ") : "—"}
              />
              <DetailRow label="Project idea" value={participant?.project_idea} multiline />
            </div>

            <button className="profile-menu__logout" onClick={onLogout}>
              Log out
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function DetailRow({ label, value, multiline }) {
  return (
    <div className={`profile-menu__detail-row ${multiline ? "profile-menu__detail-row--multiline" : ""}`}>
      <span className="profile-menu__detail-label">{label}</span>
      <span className="profile-menu__detail-value">{value || "—"}</span>
    </div>
  );
}
