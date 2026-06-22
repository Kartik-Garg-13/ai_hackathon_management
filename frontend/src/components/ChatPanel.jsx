import React, { useEffect, useRef, useState } from "react";
import GlassCard from "./GlassCard.jsx";
import { api } from "../api.js";
import "./ChatPanel.css";

export default function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    api.chatHistory().then(setMessages).catch((e) => setError(e.message));

    const ws = new WebSocket(api.chatWebSocketUrl());
    ws.onopen = () => {
      if (wsRef.current === ws) setError(null);
    };
    ws.onmessage = (event) => {
      setMessages((prev) => [...prev, JSON.parse(event.data)]);
    };
    ws.onerror = () => {
      // Ignore errors from a connection that's already been superseded
      // (e.g. React StrictMode's double-mount closing the first socket
      // mid-handshake) — only the current connection's errors matter.
      if (wsRef.current === ws) setError("Chat connection lost — refresh to reconnect.");
    };
    wsRef.current = ws;

    return () => {
      ws.close();
      if (wsRef.current === ws) wsRef.current = null;
    };
  }, []);

  function handleSend(e) {
    e.preventDefault();
    if (!draft.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ body: draft }));
    setDraft("");
  }

  return (
    <GlassCard tone="light" className="chat-panel">
      <h3 className="chat-panel__title">Team chat</h3>
      <p className="chat-panel__hint">All participants and mentors in this hackathon can see this.</p>
      {error && <div className="chat-panel__error">{error}</div>}
      <div className="chat-panel__messages">
        {messages.length === 0 && <p className="chat-panel__empty">No messages yet — say hello.</p>}
        {messages.map((m) => (
          <div key={m.id} className="chat-panel__message">
            <strong>{m.sender_name}</strong> <span className="chat-panel__role">({m.sender_role})</span>: {m.body}
          </div>
        ))}
      </div>
      <form onSubmit={handleSend} className="chat-panel__form">
        <input className="chat-panel__input" placeholder="Type a message…" value={draft} onChange={(e) => setDraft(e.target.value)} />
        <button type="submit" className="chat-panel__send">Send</button>
      </form>
    </GlassCard>
  );
}
