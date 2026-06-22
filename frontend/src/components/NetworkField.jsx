import React, { useMemo } from "react";
import { motion } from "framer-motion";

export default function NetworkField({
  density = 22,
  variant = "ambient",
  className = "",
}) {
  const nodes = useMemo(() => generateNodes(density), [density]);
  const edges = useMemo(() => generateEdges(nodes), [nodes]);

  const isActive = variant === "active";

  return (
    <svg
      className={className}
      viewBox="0 0 1000 1000"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
      style={{ width: "100%", height: "100%" }}
    >
      <defs>
        <radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={isActive ? "#5b9bd1" : "#b0e0e6"} stopOpacity="0.9" />
          <stop offset="100%" stopColor={isActive ? "#5b9bd1" : "#b0e0e6"} stopOpacity="0" />
        </radialGradient>
      </defs>

      {edges.map((edge, i) => (
        <motion.line
          key={`edge-${i}`}
          x1={edge.x1}
          y1={edge.y1}
          x2={edge.x2}
          y2={edge.y2}
          stroke={isActive ? "#4682b4" : "#4682b4"}
          strokeOpacity={isActive ? 0.45 : 0.3}
          strokeWidth={isActive ? 1.1 : 0.8}
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{
            duration: 1.6,
            delay: edge.delay,
            ease: [0.16, 1, 0.3, 1],
          }}
        />
      ))}

      {nodes.map((node, i) => (
        <g key={`node-${i}`}>
          <motion.circle
            cx={node.x}
            cy={node.y}
            r={node.r * 5.5}
            fill="url(#nodeGlow)"
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 0.7, 0.4] }}
            transition={{
              duration: 2.4,
              delay: node.delay,
              ease: "easeOut",
            }}
          />
          <motion.circle
            cx={node.x}
            cy={node.y}
            r={node.r}
            fill={isActive ? "#4682b4" : "#5b9bd1"}
            initial={{ opacity: 0, scale: 0 }}
            animate={{
              opacity: 1,
              scale: 1,
              cy: [node.y, node.y - node.drift, node.y],
            }}
            transition={{
              opacity: { duration: 0.6, delay: node.delay },
              scale: { duration: 0.6, delay: node.delay, ease: "backOut" },
              cy: {
                duration: node.floatDuration,
                delay: node.delay + 0.6,
                repeat: Infinity,
                ease: "easeInOut",
              },
            }}
          />
        </g>
      ))}
    </svg>
  );
}

function generateNodes(count) {
  const nodes = [];
  for (let i = 0; i < count; i++) {
    nodes.push({
      id: i,
      x: 40 + Math.random() * 920,
      y: 40 + Math.random() * 920,
      r: 2.2 + Math.random() * 3,
      delay: Math.random() * 1.2,
      drift: 14 + Math.random() * 22,
      floatDuration: 4 + Math.random() * 3,
    });
  }
  return nodes;
}

function generateEdges(nodes, maxDist = 220, maxEdgesPerNode = 2) {
  const edges = [];
  nodes.forEach((a, i) => {
    let connections = 0;
    nodes.forEach((b, j) => {
      if (i === j || connections >= maxEdgesPerNode) return;
      const dist = Math.hypot(a.x - b.x, a.y - b.y);
      if (dist < maxDist) {
        edges.push({
          x1: a.x,
          y1: a.y,
          x2: b.x,
          y2: b.y,
          delay: 0.3 + Math.random() * 1.4,
        });
        connections++;
      }
    });
  });
  return edges;
}
