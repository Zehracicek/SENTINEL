import { Suspense, useLayoutEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Bounds, Stars, useGLTF } from "@react-three/drei";
import * as THREE from "three";
import { ROVER_GLB_URL } from "../../utils/publicUrl";
import BindInvalidate from "./BindInvalidate";

useGLTF.preload(ROVER_GLB_URL);

function RoverMesh() {
  const gltf = useGLTF(ROVER_GLB_URL);
  const scene = useMemo(() => gltf.scene.clone(true), [gltf.scene]);
  const invalidate = useThree((s) => s.invalidate);

  useLayoutEffect(() => {
    scene.traverse((obj) => {
      if (obj.isMesh) {
        obj.castShadow = false;
        obj.receiveShadow = false;
        obj.frustumCulled = true;
      }
    });
    invalidate();
  }, [scene, invalidate]);

  return <primitive object={scene} />;
}

function ScrollCameraRig({ progressRef, roverGroupRef }) {
  const { camera } = useThree();

  useFrame(() => {
    const p = Math.min(1, Math.max(0, progressRef.current));
    const orbit = p * Math.PI * 2 * 0.9;
    const radius = 7.4 - p * 3.1;
    camera.position.x = Math.sin(orbit) * radius;
    camera.position.z = Math.cos(orbit) * radius;
    camera.position.y = 1.55 + Math.sin(p * Math.PI) * 0.95;
    camera.lookAt(0, 0.35, 0);

    if (roverGroupRef.current) {
      roverGroupRef.current.rotation.y =
        p * 0.55 + Math.sin(p * Math.PI * 2) * 0.08;
    }
  });

  return null;
}

function Scene({ progressRef }) {
  const roverGroupRef = useRef(null);

  return (
    <>
      <color attach="background" args={["#060403"]} />
      <fog attach="fog" args={["#060403", 12, 38]} />

      <ambientLight intensity={0.38} color="#c4a882" />
      <directionalLight
        position={[8, 18, 10]}
        intensity={1.2}
        color="#ffe8c8"
      />
      <directionalLight position={[-12, 6, -8]} intensity={0.32} color="#6b8fb8" />
      <hemisphereLight args={["#3d4a5c", "#1a1208", 0.22]} />

      <Stars
        radius={80}
        depth={40}
        count={420}
        factor={2}
        saturation={0}
        fade={false}
        speed={0}
      />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]}>
        <circleGeometry args={[14, 32]} />
        <meshBasicMaterial color="#1a1410" />
      </mesh>

      <group ref={roverGroupRef}>
        <Bounds fit margin={1.28}>
          <RoverMesh />
        </Bounds>
      </group>

      <ScrollCameraRig progressRef={progressRef} roverGroupRef={roverGroupRef} />
    </>
  );
}

export default function LandingRoverCanvas({ progressRef, invalidateRef, active = true }) {
  return (
    <div
      className="pointer-events-none fixed inset-0 z-0"
      aria-hidden
      style={{ visibility: active ? "visible" : "hidden" }}
    >
      <Canvas
        frameloop={active ? "demand" : "never"}
        shadows={false}
        dpr={1}
        gl={{
          antialias: false,
          alpha: false,
          powerPreference: "high-performance",
          stencil: false,
          depth: true,
        }}
        camera={{ position: [5.5, 2.2, 6.2], fov: 38, near: 0.1, far: 80 }}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.08;
          gl.outputColorSpace = THREE.SRGBColorSpace;
        }}
      >
        <BindInvalidate invalidateRef={invalidateRef} />
        <Suspense fallback={null}>
          <Scene progressRef={progressRef} />
        </Suspense>
      </Canvas>
    </div>
  );
}
