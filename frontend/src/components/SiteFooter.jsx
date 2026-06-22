import React, { useEffect, useRef, useState } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import NetworkField from "./NetworkField.jsx";
import { api } from "../api.js";
import "./SiteFooter.css";

export default function SiteFooter() {
  const ref = useRef(null);
  const [pastHackathons, setPastHackathons] = useState([]);

  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const glowY = useTransform(scrollYProgress, [0, 1], ["-14%", "14%"]);
  const dotsY = useTransform(scrollYProgress, [0, 1], ["8%", "-8%"]);

  useEffect(() => {
    api.listAllPublicHackathons()
      .then((all) => {
        const now = new Date();
        setPastHackathons(all.filter((h) => h.registration_deadline && new Date(h.registration_deadline) < now));
      })
      .catch(() => {});
  }, []);

  const gridSlots = [...pastHackathons.slice(0, 3), ...Array(Math.max(0, 4 - pastHackathons.length)).fill(null)].slice(0, 4);

  return (
    <footer className="site-footer" ref={ref}>
      <motion.div className="site-footer__glow" style={{ y: glowY }} />
      <motion.div className="site-footer__dots" style={{ y: dotsY }}>
        <NetworkField density={16} variant="ambient" />
      </motion.div>

      <motion.div
        className="site-footer__inner"
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: 0.7 }}
      >
        <div className="site-footer__col site-footer__col--hackathons">
          <h2 className="site-footer__heading">Previous hackathons conducted</h2>
          <div className="site-footer__grid">
            {gridSlots.map((h, i) =>
              h ? (
                <div key={h.id} className="site-footer__hack-card">
                  <span className="site-footer__hack-name">{h.name}</span>
                  {h.start_date && (
                    <span className="site-footer__hack-date">
                      {new Date(h.start_date).toLocaleDateString(undefined, { month: "long", year: "numeric" })}
                    </span>
                  )}
                </div>
              ) : (
                <div key={`empty-${i}`} className="site-footer__hack-card site-footer__hack-card--empty" />
              )
            )}
          </div>
        </div>

        <div className="site-footer__divider" />

        <div className="site-footer__col site-footer__col--about">
          <h2 className="site-footer__heading">About us</h2>
          <p className="site-footer__about-text">
            We're four students at Manipal University Jaipur. This started as our entry
            for the Dell Futureminds AI Hackathon — eleven real features, zero LLM calls,
            every decision explainable. It got good enough that we wanted more than a
            judging panel to see it, so here it is.
          </p>
        </div>
      </motion.div>
    </footer>
  );
}
