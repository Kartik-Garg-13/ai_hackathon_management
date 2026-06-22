import React from "react";
import { motion } from "framer-motion";
import "./GlassCard.css";

export default function GlassCard({
  children,
  className = "",
  tone = "dark", // "dark" | "light"
  hoverLift = false,
  ...props
}) {
  return (
    <motion.div
      className={`glass-card glass-card--${tone} ${hoverLift ? "glass-card--hover" : ""} ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
}
