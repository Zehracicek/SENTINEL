/**
 * Anthropic "Claude on Mars" sayfasındaki HYPERDRIVE / CASPIAN panellerinden esinlenen
 * SENTİNEL simülasyon görünümleri (orijinal kod/varlık çekilmez — yeniden üretim).
 */
import {
  Suspense,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  Bounds,
  Environment,
  GizmoHelper,
  GizmoViewcube,
  Grid,
  Line,
  Text,
  useGLTF,
} from "@react-three/drei";
import {
  motion,
  useMotionValueEvent,
  useScroll,
  useSpring,
} from "framer-motion";
import * as THREE from "three";

useGLTF.preload("/models/perseverance.glb");

function heightAt(x, z) {
  return (
    Math.sin(x * 0.45) * 0.32 +
    Math.cos(z * 0.38) * 0.28 +
    Math.sin((x + z) * 0.18) * 0.22
  );
}

function MarsRoverInBounds({ margin = 1.18, y = 0 }) {
  const gltf = useGLTF("/models/perseverance.glb");
  const scene = useMemo(() => gltf.scene.clone(true), [gltf.scene]);

  useLayoutEffect(() => {
    scene.traverse((obj) => {
      if (obj.isMesh) {
        obj.castShadow = true;
        obj.receiveShadow = true;
        if (obj.material && "envMapIntensity" in obj.material) {
          obj.material.envMapIntensity = 0.75;
        }
      }
    });
  }, [scene]);

  return (
    <group position={[0, y, 0]}>
      <Bounds fit clip margin={margin}>
        <primitive object={scene} />
      </Bounds>
    </group>
  );
}

function cyanPathPoints(seed = 0) {
  const pts = [];
  for (let i = 0; i < 48; i++) {
    const t = i / 47;
    const x = Math.sin(t * Math.PI * 1.35 + seed) * 7.5 + 1.2;
    const z = -t * 22 + 5;
    const y = 0.06 + Math.sin(t * 8 + seed) * 0.08;
    pts.push(new THREE.Vector3(x, y, z));
  }
  return pts;
}

function HyperdriveScene({ phaseRef }) {
  const pathA = useMemo(() => cyanPathPoints(0), []);
  const pathB = useMemo(() => cyanPathPoints(1.7), []);

  return (
    <>
      <color attach="background" args={["#080706"]} />
      <fog attach="fog" args={["#8f7355", 18, 52]} />

      <ambientLight intensity={0.35} color="#c4a882" />
      <directionalLight
        position={[12, 22, 8]}
        intensity={1.15}
        color="#ffe8d0"
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <directionalLight
        position={[-10, 8, -6]}
        intensity={0.25}
        color="#00F2FF"
      />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]} receiveShadow>
        <planeGeometry args={[120, 120]} />
        <meshStandardMaterial color="#5c5348" roughness={0.92} metalness={0.06} />
      </mesh>

      <Grid
        position={[0, 0.01, 0]}
        infiniteGrid
        fadeDistance={62}
        fadeStrength={4}
        cellSize={0.9}
        sectionSize={9}
        sectionColor="#146b32"
        cellColor="#1f7f40"
        sectionThickness={1.15}
        cellThickness={0.55}
      />

      <Line
        points={pathA}
        color="#40ffe8"
        lineWidth={1}
        transparent
        opacity={0.92}
      />
      <Line
        points={pathB}
        color="#5af0ff"
        lineWidth={1}
        transparent
        opacity={0.65}
      />

      <Text
        position={[pathA[12].x, 0.45, pathA[12].z]}
        fontSize={0.32}
        color="#7ee8d4"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.02}
        outlineColor="#000000"
      >
        MobSketch_03
      </Text>
      <Text
        position={[pathB[28].x, 0.45, pathB[28].z]}
        fontSize={0.3}
        color="#9cf0ff"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.02}
        outlineColor="#000000"
      >
        MobSketch_04
      </Text>

      <ScrollRig phaseRef={phaseRef}>
        <group position={[0, 0, -2]}>
          <MarsRoverInBounds margin={1.22} y={0} />
        </group>
      </ScrollRig>

      <HyperdriveCamera phaseRef={phaseRef} />
      <Environment preset="sunset" environmentIntensity={0.35} />
    </>
  );
}

/** Bölüm kaydırmasına göre rover grubunu hafifçe döndürür (zaman döngüsü yok). */
function ScrollRig({ phaseRef, children }) {
  const g = useRef(null);
  useFrame(() => {
    const p = Math.min(1, Math.max(0, phaseRef?.current ?? 0));
    if (g.current) {
      g.current.rotation.y = THREE.MathUtils.lerp(
        g.current.rotation.y,
        p * 0.65 - 0.32,
        0.08,
      );
    }
  });
  return <group ref={g}>{children}</group>;
}

function HyperdriveCamera({ phaseRef }) {
  const { camera } = useThree();
  useFrame(() => {
    const p = Math.min(1, Math.max(0, phaseRef?.current ?? 0));
    const orbit = p * Math.PI * 2.05;
    const r = 8.8 + Math.sin(p * Math.PI) * 3.1;
    const tx = Math.sin(orbit) * r;
    const tz = Math.cos(orbit) * r + 1.8;
    const ty = 2.2 + p * 3.4 + Math.sin(p * Math.PI) * 0.75;
    camera.position.lerp(new THREE.Vector3(tx, ty, tz), 0.14);
    camera.lookAt(0, 1.05 + p * 0.35, -3.2 + p * 2.4);
  });
  return null;
}

function CaspianHeightTerrain() {
  const geo = useMemo(() => {
    const g = new THREE.PlaneGeometry(30, 30, 80, 80);
    g.rotateX(-Math.PI / 2);
    const pos = g.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const z = pos.getZ(i);
      pos.setY(i, heightAt(x, z));
    }
    g.computeVertexNormals();
    return g;
  }, []);

  const redMarkers = useMemo(() => {
    const out = [];
    const rng = (i) => {
      const s = Math.sin(i * 12.9898) * 43758.5453;
      return s - Math.floor(s);
    };
    for (let i = 0; i < 55; i++) {
      const x = (rng(i) - 0.5) * 22;
      const z = (rng(i + 17) - 0.5) * 22;
      const y = heightAt(x, z) + 0.04;
      out.push([x, y, z]);
    }
    return out;
  }, []);

  return (
    <group>
      <mesh geometry={geo} receiveShadow castShadow>
        <meshStandardMaterial color="#e4e8ef" roughness={0.94} metalness={0.04} />
      </mesh>
      <mesh geometry={geo} position={[0, 0.004, 0]} renderOrder={1}>
        <meshBasicMaterial
          color="#8899aa"
          wireframe
          transparent
          opacity={0.14}
          depthWrite={false}
        />
      </mesh>
      {redMarkers.map((pos, i) => (
        <mesh key={i} position={pos} renderOrder={2}>
          <boxGeometry args={[0.09, 0.06, 0.09]} />
          <meshStandardMaterial
            color="#c41e3a"
            emissive="#5a0a14"
            emissiveIntensity={0.35}
            roughness={0.6}
          />
        </mesh>
      ))}
    </group>
  );
}

function darkArcLines() {
  const lines = [];
  for (let k = 0; k < 5; k++) {
    const pts = [];
    for (let i = 0; i < 24; i++) {
      const t = i / 23;
      const spread = (k - 2) * 0.35;
      const x = Math.sin(t * Math.PI * 0.85 + spread) * 2.8;
      const z = -t * 6.5 - 0.5;
      const y = heightAt(x, z) + 0.08;
      pts.push(new THREE.Vector3(x, y, z));
    }
    lines.push(pts);
  }
  return lines;
}

function CaspianScene({ phaseRef }) {
  const arcs = useMemo(() => darkArcLines(), []);

  return (
    <>
      <color attach="background" args={["#0a0b0d"]} />
      <fog attach="fog" args={["#0a0b0d", 14, 42]} />

      <ambientLight intensity={0.45} />
      <directionalLight position={[8, 16, 6]} intensity={0.85} castShadow />
      <directionalLight position={[-6, 4, -4]} intensity={0.2} color="#a8c4ff" />

      <CaspianHeightTerrain />

      <CaspianRoverRig phaseRef={phaseRef}>
        <group position={[0, heightAt(0, 0) + 0.15, 0]}>
          <MarsRoverInBounds margin={1.05} y={0} />
          <FovCone phaseRef={phaseRef} />
        </group>
      </CaspianRoverRig>

      {arcs.map((pts, i) => (
        <Line
          key={i}
          points={pts}
          color="#1e2228"
          lineWidth={1}
          transparent
          opacity={0.85}
        />
      ))}

      <CaspianCamera phaseRef={phaseRef} />

      <GizmoHelper alignment="top-right" margin={[72, 72]}>
        <GizmoViewcube
          opacity={0.88}
          color="#2a3344"
          hoverColor="#00F2FF"
          textColor="#e2e8f0"
          strokeColor="#0f1218"
        />
      </GizmoHelper>

      <Environment preset="city" environmentIntensity={0.25} />
    </>
  );
}

function CaspianRoverRig({ phaseRef, children }) {
  const g = useRef(null);
  useFrame(() => {
    const p = Math.min(1, Math.max(0, phaseRef?.current ?? 0));
    if (g.current) {
      g.current.rotation.y = THREE.MathUtils.lerp(
        g.current.rotation.y,
        -0.4 + p * 0.85,
        0.07,
      );
    }
  });
  return <group ref={g}>{children}</group>;
}

function FovCone({ phaseRef }) {
  const meshRef = useRef(null);
  useFrame(() => {
    const p = Math.min(1, Math.max(0, phaseRef?.current ?? 0));
    if (meshRef.current?.material) {
      meshRef.current.material.opacity = 0.08 + p * 0.22;
    }
  });
  return (
    <mesh
      ref={meshRef}
      position={[0.35, 1.05, 0.6]}
      rotation={[0.25, -0.4, 0.15]}
      renderOrder={3}
    >
      <coneGeometry args={[0.95, 2.4, 28, 1, true]} />
      <meshBasicMaterial
        color="#f5d547"
        transparent
        opacity={0.18}
        side={THREE.DoubleSide}
        depthWrite={false}
      />
    </mesh>
  );
}

function CaspianCamera({ phaseRef }) {
  const { camera } = useThree();
  useFrame(() => {
    const p = Math.min(1, Math.max(0, phaseRef?.current ?? 0));
    const orbit = -p * Math.PI * 1.75;
    const r = 9.5 + Math.cos(p * Math.PI) * 3.2;
    const tx = Math.sin(orbit) * r * 0.88 + 3.6;
    const tz = Math.cos(orbit) * r * 0.78 + 1.8;
    const ty = 3.8 + p * 2.8;
    camera.position.lerp(new THREE.Vector3(tx, ty, tz), 0.12);
    const lookY = heightAt(0, 0) + 0.85 + p * 0.25;
    camera.lookAt(-0.4 + p * 0.3, lookY, -1.2 + p * 0.9);
  });
  return null;
}

function CaspianTelemetryOverlay({ scrollP = 0 }) {
  const p =
    typeof scrollP === "number" && Number.isFinite(scrollP)
      ? Math.min(1, Math.max(0, scrollP))
      : 0;
  const j = (base, amp) => (base + (p - 0.5) * amp * 2).toFixed(3);
  return (
    <div className="pointer-events-none absolute bottom-4 left-4 z-10 max-w-[min(92vw,280px)] font-mono text-[9px] leading-relaxed text-[#7dd3a8] sm:text-[10px]">
      <p className="text-[#00F2FF]/90">X {j(2.847, 0.018)}</p>
      <p className="text-[#00F2FF]/90">Y {j(0.412, 0.012)}</p>
      <p className="text-[#00F2FF]/90">Z {j(-4.291, 0.022)}</p>
      <p className="mt-1 text-[#8b949e]">ROLL {j(0.018, 0.006)}</p>
      <p className="text-[#8b949e]">PITCH {j(-0.006, 0.005)}</p>
      <p className="text-[#8b949e]">YAW {j(1.204, 0.035)}</p>
      <p className="mt-1 text-[#506070]">LF_STEER {j(0.02, 0.014)}</p>
      <p className="text-[#506070]">RR_STEER {j(-0.01, 0.012)}</p>
    </div>
  );
}

function usePanelScrollPhase(sectionRef) {
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start 0.88", "end 0.12"],
  });
  const spring = useSpring(scrollYProgress, {
    stiffness: 88,
    damping: 32,
    mass: 0.42,
  });
  const phaseRef = useRef(0);
  const [uiP, setUiP] = useState(0);

  useMotionValueEvent(spring, "change", (v) => {
    phaseRef.current = v;
    setUiP(v);
  });
  useLayoutEffect(() => {
    const v = spring.get();
    phaseRef.current = v;
    setUiP(v);
  }, [spring]);

  return { phaseRef, uiP };
}

const panelChrome =
  "relative overflow-hidden border border-white/[0.08] bg-[#050403]/90 shadow-[0_24px_80px_-24px_rgba(0,0,0,0.85)]";

export function HyperdrivePanel() {
  const [mount, setMount] = useState(false);
  const sectionRef = useRef(null);
  const { phaseRef } = usePanelScrollPhase(sectionRef);

  return (
    <motion.section
      ref={sectionRef}
      id="mars-hyperdrive"
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.12 }}
      transition={{ duration: 0.75, ease: [0.22, 1, 0.36, 1] }}
      onViewportEnter={() => setMount(true)}
      className="relative z-10 px-4 py-12 sm:px-8 sm:py-16"
    >
      <div className={`mx-auto max-w-6xl ${panelChrome}`}>
        <p className="border-b border-[#0D1520] py-3 text-center font-mono text-[11px] font-medium uppercase tracking-[0.45em] text-[#BCC8D4]">
          HYPERDRIVE
        </p>
        <div className="relative h-[min(52vh,480px)] w-full sm:h-[min(56vh,520px)]">
          {mount && (
            <Suspense
              fallback={
                <div className="flex h-full items-center justify-center bg-[#060910] font-mono text-xs text-[#506070]">
                  Sahne yükleniyor…
                </div>
              }
            >
              <Canvas
                shadows
                dpr={[1, 1.5]}
                gl={{ antialias: true, alpha: false }}
                camera={{ position: [7, 5, 12], fov: 42, near: 0.1, far: 80 }}
                onCreated={({ gl }) => {
                  gl.toneMapping = THREE.ACESFilmicToneMapping;
                  gl.toneMappingExposure = 1.02;
                }}
              >
                <HyperdriveScene phaseRef={phaseRef} />
              </Canvas>
            </Suspense>
          )}
        </div>
        <p className="border-t border-[#0D1520] px-4 py-2 text-right font-mono text-[9px] uppercase tracking-[0.25em] text-[#3A4A5C]">
          Kaydırarak kamera ·{" "}
          <a
            href="https://www.anthropic.com/features/claude-on-mars"
            target="_blank"
            rel="noreferrer"
            className="text-[#506070] underline decoration-[#0D1520] underline-offset-2 hover:text-[#00F2FF]"
          >
            Anthropic Mars
          </a>{" "}
          tarzı (SENTİNEL yeniden üretimi)
        </p>
      </div>
    </motion.section>
  );
}

export function CaspianPanel() {
  const [mount, setMount] = useState(false);
  const sectionRef = useRef(null);
  const { phaseRef, uiP } = usePanelScrollPhase(sectionRef);

  return (
    <motion.section
      ref={sectionRef}
      id="mars-caspian"
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.12 }}
      transition={{ duration: 0.75, ease: [0.22, 1, 0.36, 1] }}
      onViewportEnter={() => setMount(true)}
      className="relative z-10 px-4 py-12 sm:px-8 sm:py-16"
    >
      <div className={`mx-auto max-w-6xl ${panelChrome}`}>
        <div className="flex items-center justify-between border-b border-[#0D1520] px-4 py-2">
          <div className="font-mono text-[9px] uppercase tracking-widest text-[#00FF88] sm:text-[10px]">
            <span className="text-[#00FF88]">costmap</span> LOCKED
            <span className="mx-2 text-[#0D1520]">|</span>
            <span className="text-[#00F2FF]">heightmap</span> LOCKED
          </div>
          <p className="font-mono text-[11px] font-medium uppercase tracking-[0.45em] text-[#BCC8D4]">
            CASPIAN
          </p>
        </div>
        <div className="relative h-[min(52vh,480px)] w-full sm:h-[min(56vh,520px)]">
          <CaspianTelemetryOverlay scrollP={uiP} />
          {mount && (
            <Suspense
              fallback={
                <div className="flex h-full items-center justify-center bg-[#060910] font-mono text-xs text-[#506070]">
                  Sahne yükleniyor…
                </div>
              }
            >
              <Canvas
                shadows
                dpr={[1, 1.5]}
                gl={{ antialias: true, alpha: false }}
                camera={{ position: [8, 6, 10], fov: 40, near: 0.1, far: 80 }}
                onCreated={({ gl }) => {
                  gl.toneMapping = THREE.ACESFilmicToneMapping;
                  gl.toneMappingExposure = 0.98;
                }}
              >
                <CaspianScene phaseRef={phaseRef} />
              </Canvas>
            </Suspense>
          )}
        </div>
        <p className="border-t border-[#0D1520] px-4 py-2 text-right font-mono text-[9px] uppercase tracking-[0.25em] text-[#3A4A5C]">
          Kaydırarak kamera · telemetri senkron · SENTİNEL yeniden üretimi
        </p>
      </div>
    </motion.section>
  );
}
