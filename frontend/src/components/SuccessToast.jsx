import React, { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./SuccessToast.css";

export default function SuccessToast({ visible, name, onDone }) {
  useEffect(() => {
    if (!visible) return;
    const timer = setTimeout(() => onDone?.(), 2200);
    return () => clearTimeout(timer);
  }, [visible, onDone]);

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="success-toast"
          role="status"
          aria-live="polite"
          initial={{ opacity: 0, y: -16, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.97 }}
          transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        >
          <span className="success-toast__icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <motion.path
                d="M5 13l4 4L19 7"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.5, delay: 0.15, ease: "easeOut" }}
              />
            </svg>
          </span>
          <div className="success-toast__text">
            <strong>Registration successful</strong>
            <span>Welcome aboard, {name || "participant"} — redirecting to your dashboard…</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
