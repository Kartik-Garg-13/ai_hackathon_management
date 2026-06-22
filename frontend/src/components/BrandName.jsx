import React from "react";
import { Link } from "react-router-dom";
import "./BrandName.css";

export function TiltedE({ className = "", glowColor = "rgba(176,224,230,0.85)" }) {
  return (
    <svg
      className={`tilted-e ${className}`}
      viewBox="0 0 38 48"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <filter id="eGlow" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <g transform="rotate(-22, 19, 24)" filter="url(#eGlow)">
        <rect x="2" y="2" width="9" height="44" rx="1.5" fill="currentColor" />
        <rect x="2" y="2" width="34" height="9" rx="1.5" fill="currentColor" />
        <rect x="2" y="20" width="27" height="8" rx="1.5" fill="currentColor" />
        <rect x="2" y="37" width="34" height="9" rx="1.5" fill="currentColor" />
      </g>
    </svg>
  );
}

export default function BrandName({ size = "md" }) {
  return (
    <Link to="/" className={`brand-name brand-name--${size} brand-name--link`} aria-label="Back to role selection">
      <span className="brand-name__d">D</span>
      <TiltedE className="brand-name__e-svg" />
      <span className="brand-name__ll">LL</span>
      <span className="brand-name__igent">igent</span>
      <span className="brand-name__minds"> minds</span>
    </Link>
  );
}
