import React, { useState } from "react";
import "./Field.css";

export function TextField({
  label,
  required = false,
  error,
  icon,
  ...props
}) {
  const [focused, setFocused] = useState(false);

  return (
    <label className={`field ${focused ? "field--focused" : ""} ${error ? "field--error" : ""}`}>
      <span className="field__label">
        {label}
        {required && <span className="field__required" aria-hidden="true"> *</span>}
        {required && <span className="visually-hidden"> (required)</span>}
      </span>
      <div className="field__control">
        {icon && <span className="field__icon">{icon}</span>}
        <input
          className="field__input"
          onFocus={(e) => {
            setFocused(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setFocused(false);
            props.onBlur?.(e);
          }}
          {...props}
        />
      </div>
      {error && <span className="field__error-text">{error}</span>}
    </label>
  );
}

export function TagsField({ label, value, onChange, placeholder }) {
  const [draft, setDraft] = useState("");
  const [focused, setFocused] = useState(false);

  function commitTag() {
    const tag = draft.trim();
    if (tag && !value.includes(tag)) {
      onChange([...value, tag]);
    }
    setDraft("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      commitTag();
    } else if (e.key === "Backspace" && draft === "" && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  }

  function removeTag(tag) {
    onChange(value.filter((t) => t !== tag));
  }

  return (
    <label className={`field field--tags ${focused ? "field--focused" : ""}`}>
      <span className="field__label">{label}</span>
      <div
        className="field__control field__control--tags"
        onClick={(e) => e.currentTarget.querySelector("input")?.focus()}
      >
        {value.map((tag) => (
          <span className="tag-chip" key={tag}>
            {tag}
            <button
              type="button"
              className="tag-chip__remove"
              onClick={() => removeTag(tag)}
              aria-label={`Remove ${tag}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          className="field__input field__input--tags"
          value={draft}
          placeholder={value.length === 0 ? placeholder : ""}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => {
            setFocused(false);
            commitTag();
          }}
        />
      </div>
      <span className="field__hint">Press Enter or comma to add a skill</span>
    </label>
  );
}

export function TextAreaField({ label, required = false, ...props }) {
  const [focused, setFocused] = useState(false);
  return (
    <label className={`field ${focused ? "field--focused" : ""}`}>
      <span className="field__label">
        {label}
        {required && <span className="field__required" aria-hidden="true"> *</span>}
      </span>
      <div className="field__control field__control--textarea">
        <textarea
          className="field__input field__input--textarea"
          onFocus={(e) => {
            setFocused(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setFocused(false);
            props.onBlur?.(e);
          }}
          {...props}
        />
      </div>
    </label>
  );
}
