import React from "react";
import "./RiskBadge.css";

export default function RiskBadge({ level, kind = "registration" }) {
  const bucket = toBucket(level);
  return (
    <span className={`risk-badge risk-badge--${bucket}`}>
      {level || "Unknown"}
    </span>
  );
}

function toBucket(level) {
  const normalized = (level || "").toLowerCase();
  if (normalized.startsWith("low")) return "low";
  if (normalized.startsWith("medium")) return "medium";
  if (normalized.startsWith("high")) return "high";
  return "neutral";
}
