import React, { useEffect, useRef, useState } from "react";
import "./TeamSearchSelect.css";

const MAX_RESULTS = 50;

export default function TeamSearchSelect({ teams, value, onChange, placeholder }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  const selectedTeam = teams.find((t) => String(t.id) === String(value));

  useEffect(() => {
    function handleClickOutside(e) {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const matches = teams
    .filter((t) => t.team_name.toLowerCase().includes(query.toLowerCase()))
    .slice(0, MAX_RESULTS);

  function handleSelect(team) {
    onChange(String(team.id));
    setQuery("");
    setOpen(false);
  }

  return (
    <div className="team-search-select" ref={rootRef}>
      <input
        className="team-search-select__input"
        type="text"
        placeholder={selectedTeam ? selectedTeam.team_name : placeholder}
        value={query}
        onFocus={() => setOpen(true)}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
      />
      {open && (
        <div className="team-search-select__menu">
          {matches.length === 0 && <div className="team-search-select__empty">No teams match.</div>}
          {matches.map((t) => (
            <button
              key={t.id}
              type="button"
              className="team-search-select__option"
              onClick={() => handleSelect(t)}
            >
              {t.team_name}
            </button>
          ))}
          {teams.length > MAX_RESULTS && matches.length === MAX_RESULTS && (
            <div className="team-search-select__hint">Keep typing to narrow down further…</div>
          )}
        </div>
      )}
    </div>
  );
}
