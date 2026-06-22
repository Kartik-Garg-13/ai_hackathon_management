import React from "react";
import "./Button.css";

export default function Button({
  children,
  variant = "primary", // "primary" | "ghost" | "outline"
  size = "md", // "sm" | "md" | "lg"
  loading = false,
  icon = null,
  className = "",
  type = "button",
  ...props
}) {
  return (
    <button
      type={type}
      className={`btn btn--${variant} btn--${size} ${loading ? "btn--loading" : ""} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? (
        <span className="btn__spinner" aria-hidden="true" />
      ) : (
        icon && <span className="btn__icon">{icon}</span>
      )}
      <span className="btn__label">{children}</span>
    </button>
  );
}
