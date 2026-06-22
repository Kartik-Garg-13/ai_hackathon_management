import React from "react";
import "./HackathonCard.css";

export default function HackathonCard({ hackathon, onManage, onGenerateLinks }) {
  return (
    <div className="hack-card">
      <div className="hack-card__main">
        <div className="hack-card__info">
          <div className="hack-card__name">{hackathon.name}</div>
          <div className="hack-card__meta">
            {hackathon.mode && <span className="hack-card__pill hack-card__pill--mode">{hackathon.mode}</span>}
            {hackathon.allow_judges && <span className="hack-card__pill">Judges</span>}
            {hackathon.allow_mentors && <span className="hack-card__pill">Mentors</span>}
          </div>
          {hackathon.description && (
            <p className="hack-card__desc">
              {hackathon.description.slice(0, 120)}{hackathon.description.length > 120 ? "…" : ""}
            </p>
          )}
        </div>
        <div className="hack-card__action">
          <button className="hack-card__register-btn" onClick={() => onManage?.(hackathon)}>
            Manage
          </button>
        </div>
      </div>
      {onGenerateLinks && (
        <div className="hack-card__prizes">
          <button
            style={{ background: "none", border: "none", color: "inherit", cursor: "pointer", padding: 0, fontSize: "inherit" }}
            onClick={() => onGenerateLinks(hackathon)}
          >
            Generate invite links
          </button>
        </div>
      )}
    </div>
  );
}
