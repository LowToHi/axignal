"use client";

import { Line, Stars } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { Suspense, useMemo, useRef } from "react";
import * as THREE from "three";

import type { Opportunity } from "./types";
import styles from "./intelligence-workspace.module.css";

const VERTEX_SHADER = `
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

const FRAGMENT_SHADER = `
uniform float uTime;
uniform float uLight;
varying vec3 vNormal;
varying vec3 vPosition;
varying vec2 vUv;

float hash(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1., 0.)), f.x),
             mix(hash(i + vec2(0., 1.)), hash(i + vec2(1., 1.)), f.x), f.y);
}

float fbm(vec2 p) {
  float value = 0.0;
  float amplitude = .55;
  for (int i = 0; i < 5; i++) {
    value += amplitude * noise(p);
    p = p * 2.03 + vec2(17.2, 9.1);
    amplitude *= .48;
  }
  return value;
}

float gridLine(float value, float width) {
  float line = abs(fract(value) - .5);
  return 1.0 - smoothstep(width, width + .035, line);
}

void main() {
  vec3 ocean = mix(vec3(.018, .075, .105), vec3(.59, .70, .76), uLight);
  vec3 land = mix(vec3(.30, .34, .29), vec3(.75, .73, .66), uLight);
  vec2 geo = vec2(vUv.x * 10.6, vUv.y * 5.4);
  float continental = fbm(geo + vec2(fbm(geo * .72), fbm(geo * .66 + 4.2)));
  float mask = smoothstep(.48, .58, continental);
  float relief = fbm(geo * 6.0);
  vec3 color = mix(ocean, land + relief * mix(vec3(.18, .12, .05), vec3(.12, .10, .07), uLight), mask);
  float latitude = gridLine(vUv.y * 18.0, .47);
  float longitude = gridLine(vUv.x * 36.0, .475);
  color += vec3(.20, .72, .74) * max(latitude, longitude) * mix(.13, .05, uLight);
  float sunlight = .38 + .85 * max(dot(normalize(vNormal), normalize(vec3(-.45, .42, 1.0))), 0.0);
  color *= sunlight;
  float city = step(.982, hash(floor(geo * 92.0))) * mask;
  color += mix(vec3(1.0, .62, .24), vec3(.88, .76, .56), uLight) * city * .92;
  float fresnel = pow(1.0 - max(dot(normalize(vNormal), vec3(0., 0., 1.)), 0.0), 2.7);
  color += vec3(.22, .76, .80) * fresnel * mix(.42, .20, uLight);
  gl_FragColor = vec4(color, .98);
}
`;

function latLonToVector(latitude: number, longitude: number, radius = 1.51) {
  const phi = (90 - latitude) * (Math.PI / 180);
  const theta = (longitude + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -(radius * Math.sin(phi) * Math.cos(theta)),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

function arcPoints(from: THREE.Vector3, to: THREE.Vector3) {
  const midpoint = from.clone().add(to).multiplyScalar(.5).normalize().multiplyScalar(1.9);
  return new THREE.QuadraticBezierCurve3(from, midpoint, to).getPoints(48);
}

type GlobeSceneProps = {
  opportunities: readonly Opportunity[];
  selectedOpportunityId: string | null;
};

function GlobeScene({ opportunities, selectedOpportunityId }: GlobeSceneProps) {
  const group = useRef<THREE.Group>(null);
  const material = useRef<THREE.ShaderMaterial>(null);
  const markers = useMemo(() => opportunities.map((item) => ({ ...item, point: latLonToVector(item.latitude, item.longitude) })), [opportunities]);
  const selectedPoint = markers.find((marker) => marker.id === selectedOpportunityId)?.point ?? markers[0]?.point;
  const arcs = useMemo(() => selectedPoint ? markers.filter((item) => item.id !== selectedOpportunityId).map((item) => ({ id: item.id, points: arcPoints(selectedPoint, item.point) })) : [], [markers, selectedOpportunityId, selectedPoint]);

  useFrame((state, delta) => {
    if (group.current && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) group.current.rotation.y += delta * .014;
    if (material.current) {
      material.current.uniforms.uTime!.value = state.clock.elapsedTime;
      const style = getComputedStyle(document.documentElement);
      material.current.uniforms.uLight!.value = document.documentElement.dataset.theme === "light" || style.colorScheme === "light" ? 1 : 0;
    }
  });

  return (
    <>
      <ambientLight intensity={.52} />
      <directionalLight position={[3, 2, 4]} intensity={1.4} color="#aee8e8" />
      <pointLight position={[-4, -2, 2]} intensity={2.0} color="#1c7d82" />
      <Stars radius={22} depth={24} count={900} factor={1.25} saturation={.05} fade speed={.12} />
      <group ref={group} rotation={[-.05, -.26, .045]}>
        <mesh>
          <sphereGeometry args={[1.48, 96, 96]} />
          <shaderMaterial ref={material} vertexShader={VERTEX_SHADER} fragmentShader={FRAGMENT_SHADER} transparent uniforms={{ uTime: { value: 0 }, uLight: { value: 0 } }} />
        </mesh>
        <mesh scale={1.009}>
          <sphereGeometry args={[1.48, 48, 48]} />
          <meshBasicMaterial color="#43c8c8" transparent opacity={.045} wireframe />
        </mesh>
        {markers.map((marker) => {
          const selected = marker.id === selectedOpportunityId;
          return (
            <group key={marker.id} position={marker.point}>
              <mesh scale={selected ? 1.35 : 1}>
                <sphereGeometry args={[.032, 18, 18]} />
                <meshBasicMaterial color={selected ? "#8ee8e4" : "#43c8c8"} />
              </mesh>
              <mesh scale={selected ? 1.5 : 1}>
                <ringGeometry args={[.052, .071, 28]} />
                <meshBasicMaterial color="#43c8c8" transparent opacity={selected ? .82 : .48} side={THREE.DoubleSide} />
              </mesh>
            </group>
          );
        })}
        {arcs.map((arc) => <Line key={arc.id} points={arc.points} color="#43c8c8" lineWidth={.8} transparent opacity={.35} />)}
      </group>
    </>
  );
}

type SemanticGlobeProps = GlobeSceneProps & {
  label: string;
  onSelect: (opportunityId: string) => void;
};

export function SemanticGlobe({ opportunities, selectedOpportunityId, label, onSelect }: SemanticGlobeProps) {
  const selected = opportunities.find((item) => item.id === selectedOpportunityId) ?? opportunities[0];
  return (
    <section className={styles.globeSurface} aria-label={label}>
      <Canvas className={styles.globeCanvas} aria-hidden="true" data-testid="semantic-globe-webgl" camera={{ position: [0, 0, 4.35], fov: 38, near: .1, far: 100 }} dpr={[1, 1.6]} gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }} fallback={<p>WebGL is unavailable. Use the accessible opportunity table.</p>}>
        <Suspense fallback={null}><GlobeScene opportunities={opportunities} selectedOpportunityId={selectedOpportunityId} /></Suspense>
      </Canvas>
      {selected ? (
        <div className={styles.globeCallout}>
          <strong>{label}</strong>
          <span>{opportunities.length} opportunities detected</span>
          <span>Selected <b>{selected.name}</b></span>
          <span>Evidence fit <b>{selected.expectedReturn ?? "Unknown"}</b></span>
          <span>Confidence <b>{selected.confidence === null ? "Unknown" : `${Math.round(selected.confidence * 100)}%`}</b></span>
        </div>
      ) : null}
      <div className={styles.legend} aria-hidden="true">
        <span>OPPORTUNITY POTENTIAL</span><i /><div><small>Very low</small><small>Medium</small><small>Very high</small><small>No data</small></div>
      </div>
      <table className={styles.srOnly}>
        <caption>{label}: accessible geographic opportunity list</caption>
        <thead><tr><th>Opportunity</th><th>Latitude</th><th>Longitude</th><th>Evidence fit</th><th>Confidence</th><th>Action</th></tr></thead>
        <tbody>{opportunities.map((opportunity) => (
          <tr key={opportunity.id}><th scope="row">{opportunity.name}</th><td>{opportunity.latitude}</td><td>{opportunity.longitude}</td><td>{opportunity.expectedReturn ?? "Unknown"}</td><td>{opportunity.confidence ?? "Unknown"}</td><td><button type="button" onClick={() => onSelect(opportunity.id)}>Select {opportunity.name}</button></td></tr>
        ))}</tbody>
      </table>
    </section>
  );
}
