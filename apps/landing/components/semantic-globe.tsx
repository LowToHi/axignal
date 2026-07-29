"use client";

import { Line, Stars } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { Suspense, useMemo, useRef } from "react";
import * as THREE from "three";
import { citySignals } from "@/lib/landing-data";

type SemanticGlobeProps = {
  activeStep: number;
  reducedMotion: boolean;
};

const vertexShader = `
  varying vec3 vNormal;
  varying vec3 vPosition;
  varying vec2 vUv;

  void main() {
    vNormal = normalize(normalMatrix * normal);
    vPosition = position;
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const fragmentShader = `
  uniform float uTime;
  uniform float uSignal;
  varying vec3 vNormal;
  varying vec3 vPosition;
  varying vec2 vUv;

  float gridLine(float value, float width) {
    float line = abs(fract(value) - 0.5);
    return 1.0 - smoothstep(width, width + 0.035, line);
  }

  void main() {
    vec3 base = vec3(0.018, 0.047, 0.058);
    vec3 ocean = vec3(0.025, 0.095, 0.108);
    vec3 signal = vec3(0.263, 0.784, 0.784);

    float latitude = gridLine(vUv.y * 18.0, 0.47);
    float longitude = gridLine(vUv.x * 36.0, 0.475);
    float grid = max(latitude, longitude) * 0.16;

    float continents = sin(vPosition.x * 9.0 + sin(vPosition.y * 7.0)) *
      cos(vPosition.z * 8.0 - vPosition.y * 3.0);
    continents = smoothstep(0.08, 0.62, continents);

    float pulse = 0.5 + 0.5 * sin(uTime * 0.45 + vPosition.y * 7.0);
    float fresnel = pow(1.0 - max(dot(normalize(vNormal), vec3(0.0, 0.0, 1.0)), 0.0), 2.4);

    vec3 color = mix(base, ocean, continents * 0.7);
    color += signal * grid;
    color += signal * fresnel * (0.20 + uSignal * 0.12);
    color += signal * pulse * continents * 0.025 * uSignal;

    float alpha = 0.96;
    gl_FragColor = vec4(color, alpha);
  }
`;

function latLonToVector(latitude: number, longitude: number, radius = 1.48) {
  const phi = (90 - latitude) * (Math.PI / 180);
  const theta = (longitude + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -(radius * Math.sin(phi) * Math.cos(theta)),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

function arcPoints(from: THREE.Vector3, to: THREE.Vector3) {
  const midpoint = from.clone().add(to).multiplyScalar(0.5).normalize().multiplyScalar(1.9);
  const curve = new THREE.QuadraticBezierCurve3(from, midpoint, to);
  return curve.getPoints(48);
}

function GlobeScene({ activeStep, reducedMotion }: SemanticGlobeProps) {
  const group = useRef<THREE.Group>(null);
  const material = useRef<THREE.ShaderMaterial>(null);
  const markers = useMemo(
    () => citySignals.map((signal) => ({ ...signal, point: latLonToVector(signal.latitude, signal.longitude) })),
    []
  );
  const arcs = useMemo(() => {
    const madrid = markers.find((marker) => marker.id === "madrid")?.point;
    if (!madrid) return [];
    return markers
      .filter((marker) => marker.id !== "madrid")
      .map((marker) => ({
        id: `madrid-${marker.id}`,
        points: arcPoints(madrid, marker.point)
      }));
  }, [markers]);

  useFrame((state, delta) => {
    if (group.current) {
      const targetY = -0.22 + activeStep * 0.075;
      group.current.rotation.y = THREE.MathUtils.damp(group.current.rotation.y, targetY, 3.5, delta);
      group.current.rotation.x = THREE.MathUtils.damp(
        group.current.rotation.x,
        activeStep > 4 ? 0.08 : -0.05,
        3.5,
        delta
      );
      if (!reducedMotion) group.current.rotation.y += delta * 0.018;
    }
    if (material.current) {
      material.current.uniforms.uTime.value = state.clock.elapsedTime;
      material.current.uniforms.uSignal.value = Math.min(1.4, 0.35 + activeStep * 0.16);
    }
  });

  const visibleSignals = Math.max(1, Math.min(markers.length, activeStep - 1));

  return (
    <>
      <ambientLight intensity={0.45} />
      <directionalLight position={[3, 2, 4]} intensity={1.4} color="#aee8e8" />
      <pointLight position={[-4, -2, 2]} intensity={2.2} color="#1c7d82" />
      <Stars radius={22} depth={24} count={800} factor={1.2} saturation={0.05} fade speed={0.15} />
      <group ref={group} rotation={[-0.05, -0.22, 0.05]}>
        <mesh>
          <sphereGeometry args={[1.45, 96, 96]} />
          <shaderMaterial
            ref={material}
            vertexShader={vertexShader}
            fragmentShader={fragmentShader}
            transparent
            uniforms={{
              uTime: { value: 0 },
              uSignal: { value: 0.35 }
            }}
          />
        </mesh>

        <mesh scale={1.012}>
          <sphereGeometry args={[1.45, 48, 48]} />
          <meshBasicMaterial color="#43c8c8" transparent opacity={0.055} wireframe />
        </mesh>

        {markers.map((marker, index) => {
          const visible = index < visibleSignals || activeStep >= 3;
          return (
            <group key={marker.id} position={marker.point}>
              <mesh scale={visible ? 1 : 0.001}>
                <sphereGeometry args={[0.032, 18, 18]} />
                <meshBasicMaterial color={marker.state === "CONTRADICTED" ? "#d79b63" : "#7fe4df"} />
              </mesh>
              <mesh scale={visible ? 1 : 0.001}>
                <ringGeometry args={[0.055, 0.072, 28]} />
                <meshBasicMaterial
                  color={marker.state === "CONTRADICTED" ? "#d79b63" : "#43c8c8"}
                  transparent
                  opacity={0.58}
                  side={THREE.DoubleSide}
                />
              </mesh>
            </group>
          );
        })}

        {arcs.map((arc, index) => (
          <Line
            key={arc.id}
            points={arc.points}
            color={index === 0 ? "#7fe4df" : "#3f9da1"}
            lineWidth={activeStep >= 3 ? 1.25 : 0.1}
            transparent
            opacity={activeStep >= 3 ? 0.62 : 0}
          />
        ))}
      </group>
    </>
  );
}

export function SemanticGlobe({ activeStep, reducedMotion }: SemanticGlobeProps) {
  return (
    <div className="semantic-globe" data-testid="semantic-globe" aria-hidden="true">
      <Canvas
        camera={{ position: [0, 0, 4.35], fov: 38, near: 0.1, far: 100 }}
        dpr={[1, 1.6]}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        fallback={<div className="globe-fallback" data-testid="globe-fallback" />}
      >
        <Suspense fallback={null}>
          <GlobeScene activeStep={activeStep} reducedMotion={reducedMotion} />
        </Suspense>
      </Canvas>
    </div>
  );
}
