import { Suspense, useLayoutEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  Bounds,
  Environment,
  Stars,
  useGLTF,
} from "@react-three/drei";
import * as THREE from "three";

useGLTF.preload("/models/perseverance.glb");

function RoverMesh() {
  const gltf = useGLTF("/models/perseverance.glb");
  const scene = useMemo(() => gltf.scene.clone(true), [gltf.scene]);

  useLayoutEffect(() => {
    scene.traverse((obj) => {
      if (obj.isMesh) {
        obj.castShadow = true;
        obj.receiveShadow = true;
        if (obj.material && "envMapIntensity" in obj.material) {
          obj.material.envMapIntensity = 0.85;
        }
      }
    });
  }, [scene]);

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

      <ambientLight intensity={0.28} color="#c4a882" />
      <directionalLight
        position={[8, 18, 10]}
        intensity={1.35}
        color="#ffe8c8"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-far={40}
        shadow-camera-near={1}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
      />
      <directionalLight
        position={[-12, 6, -8]}
        intensity={0.35}
        color="#6b8fb8"
      />
      <hemisphereLight args={["#3d4a5c", "#1a1208", 0.22]} />

      <Stars
        radius={120}
        depth={60}
        count={5000}
        factor={2.2}
        saturation={0}
        fade
        speed={0.25}
      />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]} receiveShadow>
        <circleGeometry args={[14, 64]} />
        <meshStandardMaterial
          color="#1a1410"
          roughness={0.94}
          metalness={0.04}
        />
      </mesh>

      <group ref={roverGroupRef}>
        <Bounds fit clip observe margin={1.28}>
          <group position={[0, 0, 0]}>
            <RoverMesh />
          </group>
        </Bounds>
      </group>

      <ScrollCameraRig progressRef={progressRef} roverGroupRef={roverGroupRef} />

      <Environment preset="night" environmentIntensity={0.45} />
    </>
  );
}

export default function LandingRoverCanvas({ progressRef }) {
  return (
    <div
      className="pointer-events-none fixed inset-0 z-0"
      aria-hidden
    >
      <Canvas
        shadows
        dpr={[
          1,
          typeof window !== "undefined"
            ? Math.min(window.devicePixelRatio || 1, 1.65)
            : 1,
        ]}
        gl={{
          antialias: true,
          alpha: false,
          powerPreference: "high-performance",
        }}
        camera={{ position: [5.5, 2.2, 6.2], fov: 38, near: 0.1, far: 120 }}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.08;
          gl.outputColorSpace = THREE.SRGBColorSpace;
        }}
      >
        <Suspense fallback={null}>
          <Scene progressRef={progressRef} />
        </Suspense>
      </Canvas>
    </div>
  );
}
