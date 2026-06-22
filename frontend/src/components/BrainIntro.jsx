import React, { useEffect, useMemo, useRef, useState, Suspense } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import * as THREE from "three";
import BrandName from "./BrandName.jsx";
import "./BrainIntro.css";

const FEATURES = [
  { num: "01", title: "Registration Intelligence", desc: "Fraud, duplicate & risk scoring on signup" },
  { num: "02", title: "Reviewer Assignment", desc: "Matches judges to projects by expertise" },
  { num: "03", title: "Bias Detection & Fairness", desc: "Flags skewed reviewer scoring patterns" },
  { num: "04", title: "AI Judge Assistant", desc: "Scores decks + GitHub repo health together" },
  { num: "05", title: "Hackathon Copilot", desc: "Instant answers from the FAQ knowledge base" },
  { num: "06", title: "Burnout Detection", desc: "Spots inactive teams before they stall" },
  { num: "07", title: "Smart Reviewer Rotation", desc: "Rebalances harsh vs. lenient scoring" },
  { num: "08", title: "AI Mentor Matching", desc: "TF-IDF matches questions to mentor expertise" },
  { num: "09", title: "Judge Dashboard", desc: "Live view of teams, scores & categories" },
  { num: "10", title: "Project Similarity Detector", desc: "Clusters near-duplicate project ideas" },
  { num: "11", title: "Live Plagiarism Detection", desc: "AST & file-diff comparison across repos" },
];

const FEATURE_NODE_INDEXES = [5, 35, 70, 100, 118, 135, 165, 200, 230, 250, 268];

const DARK_BG = [5, 10, 19];
const LIGHT_BG = [240, 248, 255];

const BUILD_DURATION = 2200;
const AUTO_CYCLE_STEP = 1600;

export default function BrainIntro() {
  const motionRef = useRef({ entrance: 0, build: 0 });
  const heroRef = useRef(null);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [pinnedFeature, setPinnedFeature] = useState(null);
  const [autoIndex, setAutoIndex] = useState(0);
  const [userHovering, setUserHovering] = useState(false);

  useEffect(() => {
    let raf;
    const start = performance.now();
    const DURATION = 1200;
    const tick = (now) => {
      const t = Math.min(1, (now - start) / DURATION);
      motionRef.current.entrance = easeOutCubic(t);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => {
    let raf;
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - start) / BUILD_DURATION);
      motionRef.current.build = easeInOutCubic(t);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      if (!userHovering && pinnedFeature === null) {
        setAutoIndex((i) => (i + 1) % FEATURES.length);
      }
    }, AUTO_CYCLE_STEP);
    return () => clearInterval(interval);
  }, [userHovering, pinnedFeature]);

  useEffect(() => {
    function onScroll() {
      const el = heroRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const p = Math.min(1, Math.max(0, -rect.top / rect.height));
      setScrollProgress(p);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const activeFeature = pinnedFeature !== null ? pinnedFeature : autoIndex;
  const fadeOpacity = 1 - smoothstep(0.45, 0.95, scrollProgress);
  const bg = lerpColor(DARK_BG, LIGHT_BG, smoothstep(0.4, 0.95, scrollProgress));

  return (
    <div className="brain-hero" ref={heroRef} style={{ backgroundColor: `rgb(${bg[0]}, ${bg[1]}, ${bg[2]})` }}>
      <div className="brain-intro__bg" style={{ opacity: fadeOpacity }} />
      <div className="brain-intro__pulse" style={{ opacity: fadeOpacity }} />
      <div className="brain-intro__pulse brain-intro__pulse--2" style={{ opacity: fadeOpacity }} />

      <div className="brain-intro__canvas" style={{ opacity: fadeOpacity }}>
        <Canvas camera={{ position: [0, 0, 8], fov: 45 }} dpr={[1, 1.5]} gl={{ antialias: true, alpha: true }}>
          <Suspense fallback={null}>
            <Scene
              motionRef={motionRef}
              activeFeature={activeFeature}
              onPin={setPinnedFeature}
              onHoverChange={setUserHovering}
            />
            <EffectComposer multisampling={0}>
              <Bloom intensity={0.45} luminanceThreshold={0.55} luminanceSmoothing={0.15} radius={0.3} />
            </EffectComposer>
          </Suspense>
        </Canvas>
      </div>

      <div className="brain-intro__brand brain-intro__brand--visible" style={{ opacity: fadeOpacity }}>
        <BrandName size="sm" />
      </div>

      <div className="brain-intro__showcase brain-intro__showcase--visible" style={{ opacity: fadeOpacity }}>
        <span className="brain-intro__showcase-num">{FEATURES[activeFeature].num}</span>
        <span className="brain-intro__showcase-title">{FEATURES[activeFeature].title}</span>
        <span className="brain-intro__showcase-desc">{FEATURES[activeFeature].desc}</span>
        <div className="brain-intro__dots">
          {FEATURES.map((f, i) => (
            <span
              key={f.num}
              className={`brain-intro__dot ${activeFeature === i ? "brain-intro__dot--active" : ""}`}
              onClick={() => setPinnedFeature(i)}
            />
          ))}
        </div>
      </div>

      <div
        className="brain-intro__scrollhint"
        style={{ opacity: fadeOpacity * (scrollProgress < 0.04 ? 1 : 0) }}
      >
        <span>Scroll to continue</span>
        <div className="brain-intro__scrollhint-arrow">⌄</div>
      </div>
    </div>
  );
}

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3);
}

function easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function smoothstep(edge0, edge1, x) {
  const t = Math.min(1, Math.max(0, (x - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
}

function lerpColor(a, b, t) {
  return [
    Math.round(a[0] + (b[0] - a[0]) * t),
    Math.round(a[1] + (b[1] - a[1]) * t),
    Math.round(a[2] + (b[2] - a[2]) * t),
  ];
}

function radius(p) {
  return Math.hypot(p[0], p[1], p[2]);
}

function Scene({ motionRef, activeFeature, onPin, onHoverChange }) {
  const groupRef = useRef();
  const { camera, gl } = useThree();
  const pointer = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const dom = gl.domElement;
    const handleMove = (e) => {
      const rect = dom.getBoundingClientRect();
      pointer.current.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.current.y = ((e.clientY - rect.top) / rect.height) * 2 - 1;
    };
    dom.addEventListener("pointermove", handleMove);
    return () => dom.removeEventListener("pointermove", handleMove);
  }, [gl]);

  useFrame(() => {
    const { entrance } = motionRef.current;

    camera.position.z = THREE.MathUtils.lerp(9.5, 5.6, entrance);
    camera.position.x = THREE.MathUtils.lerp(0, -pointer.current.x * 0.3, entrance);
    camera.lookAt(0, 0, 0);

    if (groupRef.current) {
      const t = performance.now() / 1000;
      const targetY = t * 0.12 + pointer.current.x * 0.35;
      const targetX = pointer.current.y * 0.22;
      groupRef.current.rotation.y += (targetY - groupRef.current.rotation.y) * 0.06;
      groupRef.current.rotation.x += (targetX - groupRef.current.rotation.x) * 0.06;
      const heartbeat = 1 + Math.sin(t * 1.1) * 0.018 + Math.sin(t * 2.7) * 0.006;
      const s = THREE.MathUtils.lerp(0.55, 1, entrance) * heartbeat;
      groupRef.current.scale.setScalar(s);
    }
  });

  return (
    <group>
      <fog attach="fog" args={["#0a1626", 9, 16]} />
      <ambientLight intensity={0.3} />
      <pointLight position={[5, 5, 5]} intensity={1.4} color="#5b9bd1" />
      <pointLight position={[-5, -3, -4]} intensity={0.8} color="#b0e0e6" />
      <pointLight position={[0, -4, 3]} intensity={0.5} color="#4682b4" />
      <group ref={groupRef}>
        <RevealAfterBuild motionRef={motionRef} threshold={0.5}>
          <GlowHalo />
        </RevealAfterBuild>
        <Edges motionRef={motionRef} />
        <RevealAfterBuild motionRef={motionRef} threshold={0.5}>
          <SignalPulses />
          <Sparks />
        </RevealAfterBuild>
        <DecorativeNodes motionRef={motionRef} />
        <RevealAfterBuild motionRef={motionRef} threshold={0.35}>
          <FeatureNodes activeFeature={activeFeature} onPin={onPin} onHoverChange={onHoverChange} />
        </RevealAfterBuild>
      </group>
    </group>
  );
}

function RevealAfterBuild({ motionRef, threshold, children }) {
  const [show, setShow] = useState(false);
  useFrame(() => {
    if (!show && motionRef.current.build >= threshold) setShow(true);
  });
  return show ? children : null;
}

function makeGlowTexture() {
  const size = 128;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  const grad = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grad.addColorStop(0, "rgba(255,255,255,1)");
  grad.addColorStop(0.4, "rgba(255,255,255,0.45)");
  grad.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, size, size);
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  return tex;
}

function GlowHalo() {
  const texture = useMemo(() => makeGlowTexture(), []);
  return (
    <sprite scale={[2.0, 1.8, 1]} position={[0, 0, -0.6]}>
      <spriteMaterial
        map={texture}
        color="#3f6e96"
        transparent
        opacity={0.16}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </sprite>
  );
}

function makeCrossTexture() {
  const size = 64;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  const c = size / 2;
  ctx.strokeStyle = "rgba(255,255,255,0.95)";
  ctx.lineWidth = 3;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(c - 14, c);
  ctx.lineTo(c + 14, c);
  ctx.moveTo(c, c - 14);
  ctx.lineTo(c, c + 14);
  ctx.stroke();
  ctx.beginPath();
  ctx.fillStyle = "rgba(255,255,255,0.95)";
  ctx.arc(c, c, 2.4, 0, Math.PI * 2);
  ctx.fill();
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  return tex;
}

function SignalPulses() {
  const texture = useMemo(() => makeGlowTexture(), []);
  const count = 28;
  const refs = useRef([]);
  const picks = useMemo(() => {
    const arr = [];
    const step = Math.max(1, Math.floor(SORTED_EDGES.length / count));
    const colors = ["#eaf6ff", "#8fd4e8", "#bfe9ff"];
    for (let i = 0; i < count; i++) {
      const edge = SORTED_EDGES[(i * step) % SORTED_EDGES.length];
      arr.push({ edge, speed: 0.35 + (i % 6) * 0.1, offset: i / count, color: colors[i % colors.length] });
    }
    return arr;
  }, []);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    picks.forEach((p, i) => {
      const mesh = refs.current[i];
      if (!mesh || !p.edge) return;
      const [a, b] = p.edge;
      const u = (t * p.speed + p.offset) % 1;
      mesh.position.set(
        a[0] + (b[0] - a[0]) * u,
        a[1] + (b[1] - a[1]) * u,
        a[2] + (b[2] - a[2]) * u
      );
      mesh.material.opacity = Math.sin(u * Math.PI) * 1.0;
    });
  });

  return (
    <group>
      {picks.map((p, i) => (
        <sprite key={i} ref={(el) => (refs.current[i] = el)} scale={[0.13, 0.13, 1]}>
          <spriteMaterial
            map={texture}
            color={p.color}
            transparent
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </sprite>
      ))}
    </group>
  );
}

function Sparks() {
  const texture = useMemo(() => makeGlowTexture(), []);
  const count = 9;
  const refs = useRef([]);
  const state = useMemo(
    () =>
      Array.from({ length: count }, () => ({
        edge: SORTED_EDGES[Math.floor(Math.random() * SORTED_EDGES.length)],
        start: Math.random() * 2,
        duration: 0.35 + Math.random() * 0.3,
        nextAt: Math.random() * 2,
      })),
    []
  );

  useFrame((stateClock) => {
    const t = stateClock.clock.elapsedTime;
    state.forEach((s, i) => {
      const mesh = refs.current[i];
      if (!mesh) return;
      const elapsed = t - s.nextAt;
      if (elapsed < 0) {
        mesh.material.opacity = 0;
        return;
      }
      const u = elapsed / s.duration;
      if (u >= 1) {
        s.edge = SORTED_EDGES[Math.floor(Math.random() * SORTED_EDGES.length)];
        s.duration = 0.3 + Math.random() * 0.35;
        s.nextAt = t + 0.4 + Math.random() * 1.6;
        mesh.material.opacity = 0;
        return;
      }
      const [a, b] = s.edge;
      const mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
      mesh.position.set(...mid);
      mesh.material.opacity = Math.sin(u * Math.PI) * 1.6;
    });
  });

  return (
    <group>
      {state.map((_, i) => (
        <sprite key={i} ref={(el) => (refs.current[i] = el)} scale={[0.22, 0.22, 1]}>
          <spriteMaterial
            map={texture}
            color="#ffffff"
            transparent
            opacity={0}
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </sprite>
      ))}
    </group>
  );
}

function buildBrainNodes() {
  const nodes = [];
  const colors = ["#b0e0e6", "#5b9bd1", "#4682b4"];
  const golden = Math.PI * (3 - Math.sqrt(5));
  const perHemisphere = 130;

  [-1, 1].forEach((side) => {
    for (let i = 0; i < perHemisphere; i++) {
      const t = i / (perHemisphere - 1);
      const yRaw = 1 - t * 1.55;
      const radiusAtY = Math.sqrt(Math.max(0, 1 - yRaw * yRaw));
      const theta = golden * i;

      let lx = Math.cos(theta) * radiusAtY;
      let lz = Math.sin(theta) * radiusAtY;

      const ripple = 1 + 0.045 * Math.sin(theta * 5 + yRaw * 6) + 0.03 * Math.cos(theta * 9 - yRaw * 4);

      const frontTaper = 1 - 0.12 * Math.max(0, lz);
      const x = (0.18 + lx * 0.78 * frontTaper) * side * 1.35 * ripple;
      const y = (yRaw * 0.95 - 0.05) * 1.15 * ripple;
      const z = lz * 1.25 * ripple;

      nodes.push({
        pos: [x, y, z],
        r: 0.028 + (i % 5) * 0.006,
        color: colors[i % colors.length],
      });
    }
  });

  for (let i = 0; i < 24; i++) {
    const a = (i / 24) * Math.PI * 2;
    const rad = 0.42 + (i % 3) * 0.05;
    nodes.push({
      pos: [Math.cos(a) * rad, -0.95 + Math.sin(a) * 0.16, 0.62 + Math.cos(a * 2) * 0.12],
      r: 0.024,
      color: colors[i % colors.length],
    });
  }

  for (let i = 0; i < 8; i++) {
    nodes.push({
      pos: [0.02 * (i % 2 ? 1 : -1), -1.15 - i * 0.06, 0.32],
      r: 0.022,
      color: colors[i % colors.length],
    });
  }

  return nodes;
}

const NODES = buildBrainNodes();
const FEATURE_INDEX_SET = new Set(FEATURE_NODE_INDEXES);

function buildEdges(nodes, maxDist = 0.26) {
  const edges = [];
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i].pos;
      const b = nodes[j].pos;
      const d = Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
      if (d < maxDist) edges.push([a, b]);
    }
  }
  return edges;
}

const SORTED_EDGES = buildEdges(NODES).sort(
  (e1, e2) => Math.max(radius(e1[0]), radius(e1[1])) - Math.max(radius(e2[0]), radius(e2[1]))
);
const SORTED_DECORATIVE = NODES.filter((_, i) => !FEATURE_INDEX_SET.has(i)).sort(
  (a, b) => radius(a.pos) - radius(b.pos)
);

function Edges({ motionRef }) {
  const meshRef = useRef();

  const geometry = useMemo(() => {
    const positions = new Float32Array(SORTED_EDGES.length * 6);
    SORTED_EDGES.forEach(([a, b], i) => {
      positions.set([a[0], a[1], a[2], b[0], b[1], b[2]], i * 6);
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geo.setDrawRange(0, 0);
    return geo;
  }, []);

  useFrame(() => {
    if (!meshRef.current) return;
    const vertexCount = Math.floor(SORTED_EDGES.length * 2 * motionRef.current.build);
    meshRef.current.geometry.setDrawRange(0, vertexCount - (vertexCount % 2));
  });

  return (
    <lineSegments ref={meshRef} geometry={geometry}>
      <lineBasicMaterial
        color="#8fd4e8"
        transparent
        opacity={0.55}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </lineSegments>
  );
}

function DecorativeNodes({ motionRef }) {
  const texture = useMemo(() => makeGlowTexture(), []);
  const meshRef = useRef();
  const materialRef = useRef();

  const geometry = useMemo(() => {
    const pos = new Float32Array(SORTED_DECORATIVE.length * 3);
    const col = new Float32Array(SORTED_DECORATIVE.length * 3);
    SORTED_DECORATIVE.forEach((n, i) => {
      pos.set(n.pos, i * 3);
      const c = new THREE.Color(n.color);
      col.set([c.r, c.g, c.b], i * 3);
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
    geo.setDrawRange(0, 0);
    return geo;
  }, []);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.geometry.setDrawRange(0, Math.floor(SORTED_DECORATIVE.length * motionRef.current.build));
    }
    if (materialRef.current) {
      const t = state.clock.elapsedTime;
      materialRef.current.size = 0.05 + Math.sin(t * 1.6) * 0.005;
    }
  });

  return (
    <points ref={meshRef} geometry={geometry}>
      <pointsMaterial
        ref={materialRef}
        size={0.05}
        map={texture}
        vertexColors
        transparent
        opacity={0.8}
        depthWrite={false}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

function FeatureConstellation() {
  const geometry = useMemo(() => {
    const segs = [];
    FEATURE_NODE_INDEXES.forEach((idx, i) => {
      const a = NODES[idx].pos;
      const dists = FEATURE_NODE_INDEXES.map((otherIdx, j) => {
        if (j === i) return Infinity;
        const b = NODES[otherIdx].pos;
        return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
      });
      const order = dists
        .map((d, j) => [d, j])
        .sort((p, q) => p[0] - q[0])
        .slice(0, 2);
      order.forEach(([, j]) => {
        if (j > i) segs.push([a, NODES[FEATURE_NODE_INDEXES[j]].pos]);
      });
    });
    const positions = new Float32Array(segs.length * 6);
    segs.forEach(([a, b], i) => positions.set([a[0], a[1], a[2], b[0], b[1], b[2]], i * 6));
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return geo;
  }, []);

  return (
    <lineSegments geometry={geometry}>
      <lineBasicMaterial color="#e9f4fb" transparent opacity={0.55} />
    </lineSegments>
  );
}

function FeatureNodes({ activeFeature, onPin, onHoverChange }) {
  const [hovered, setHovered] = useState(null);
  const crossTexture = useMemo(() => makeCrossTexture(), []);

  return (
    <group>
      <FeatureConstellation />
      {FEATURE_NODE_INDEXES.map((idx, featureIdx) => {
        const n = NODES[idx];
        const isActive = hovered === featureIdx || activeFeature === featureIdx;
        return (
          <group key={idx} position={n.pos}>
            <sprite
              scale={isActive ? [0.4, 0.4, 1] : [0.26, 0.26, 1]}
              onPointerOver={(e) => {
                e.stopPropagation();
                setHovered(featureIdx);
                onHoverChange(true);
              }}
              onPointerOut={(e) => {
                e.stopPropagation();
                setHovered((h) => (h === featureIdx ? null : h));
                onHoverChange(false);
              }}
              onClick={(e) => {
                e.stopPropagation();
                onPin(featureIdx);
              }}
            >
              <spriteMaterial
                map={crossTexture}
                color={isActive ? "#ffffff" : n.color}
                transparent
                opacity={isActive ? 1 : 0.85}
                depthWrite={false}
                blending={THREE.AdditiveBlending}
              />
            </sprite>
            <Html distanceFactor={6} center style={{ pointerEvents: "none" }}>
              <div className={`brain-node-tooltip ${isActive ? "brain-node-tooltip--active" : ""}`}>
                <span className="brain-node-tooltip__num">{FEATURES[featureIdx].num}</span>
              </div>
            </Html>
          </group>
        );
      })}
    </group>
  );
}
