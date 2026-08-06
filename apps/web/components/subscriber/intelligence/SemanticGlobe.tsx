"use client";

import { Html, OrbitControls, useTexture } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  Component,
  memo,
  Suspense,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ErrorInfo,
  type ReactNode,
} from "react";
import * as THREE from "three";

import {
  createBoundaryGeometry,
  latLonToVector,
  northUpFocusRotation,
  type GeoJsonDocument,
} from "./globe-geometry";
import type { Opportunity } from "./types";
import styles from "./intelligence-workspace.module.css";

const GLOBE_ASSETS = {
  desktop: {
    albedo: "/globe/earth-albedo.webp",
    clouds: "/globe/earth-clouds.webp",
  },
  constrained: {
    albedo: "/globe/earth-albedo-mobile.webp",
    clouds: "/globe/earth-clouds-mobile.webp",
  },
  boundaries: "/globe/europe-boundaries-50m.geojson",
} as const;

// Keep the empty-state globe aligned to the geographic frame as well: yaw is
// allowed to choose the default longitude, but pitch and roll stay at zero.
const DEFAULT_GLOBE_ROTATION = new THREE.Euler(0, -1.72, 0);

function rotationForInvestigation(opportunities: readonly Opportunity[]) {
  if (opportunities.length === 0) return DEFAULT_GLOBE_ROTATION.clone();

  const centre = new THREE.Vector3();
  opportunities.forEach((opportunity) => {
    centre.add(
      latLonToVector(opportunity.latitude, opportunity.longitude, 1).normalize(),
    );
  });
  if (centre.lengthSq() < 0.0001) return DEFAULT_GLOBE_ROTATION.clone();

  return northUpFocusRotation(centre, DEFAULT_GLOBE_ROTATION);
}

const ATMOSPHERE_VERTEX_SHADER = `
  varying vec3 vNormal;
  void main() {
    vNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const ATMOSPHERE_FRAGMENT_SHADER = `
  uniform vec3 uColour;
  varying vec3 vNormal;
  void main() {
    float fresnel = pow(1.0 - max(dot(normalize(vNormal), vec3(0.0, 0.0, 1.0)), 0.0), 3.25);
    gl_FragColor = vec4(uColour, fresnel * 0.56);
  }
`;

const CLOUD_VERTEX_SHADER = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const CLOUD_FRAGMENT_SHADER = `
  uniform sampler2D uClouds;
  uniform float uOpacity;
  varying vec2 vUv;
  void main() {
    vec3 sampleColour = texture2D(uClouds, vUv).rgb;
    float luminance = dot(sampleColour, vec3(0.2126, 0.7152, 0.0722));
    float alpha = smoothstep(0.18, 0.7, luminance) * uOpacity;
    gl_FragColor = vec4(mix(vec3(0.76, 0.88, 0.9), sampleColour, 0.62), alpha);
  }
`;

type GlobeSceneProps = {
  opportunities: readonly Opportunity[];
  selectedOpportunityId: string | null;
  label: string;
  rotation: THREE.Euler;
  onContextFailure: () => void;
  onSelect: (opportunityId: string) => void;
};

function isConstrainedDevice() {
  const memory = (navigator as Navigator & { deviceMemory?: number })
    .deviceMemory;
  return (
    window.innerWidth < 768 ||
    window.devicePixelRatio > 2 ||
    (memory !== undefined && memory <= 4)
  );
}

function configureTexture(
  texture: THREE.Texture,
  renderer: THREE.WebGLRenderer,
  anisotropy: number,
) {
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.anisotropy = Math.min(
    anisotropy,
    renderer.capabilities.getMaxAnisotropy(),
  );
  texture.needsUpdate = true;
}

function semanticMarkerColour(opportunity: Opportunity) {
  const level = opportunity.level.toLowerCase();
  if (level.includes("high")) return "#00e1cf";
  if (level.includes("medium")) return "#f5b942";
  if (level.includes("low")) return "#7f8b91";
  return "#8d6cff";
}

function surfaceOrientation(point: THREE.Vector3) {
  return new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 0, 1),
    point.clone().normalize(),
  );
}

function EarthSurface({ constrained }: { constrained: boolean }) {
  const { gl } = useThree();
  const assets = constrained ? GLOBE_ASSETS.constrained : GLOBE_ASSETS.desktop;
  const [albedo, clouds] = useTexture([
    assets.albedo,
    assets.clouds,
  ] as const) as [THREE.Texture, THREE.Texture];
  const cloudMaterial = useRef<THREE.ShaderMaterial>(null);

  useEffect(() => {
    configureTexture(albedo, gl, constrained ? 3 : 8);
    configureTexture(clouds, gl, constrained ? 2 : 4);
  }, [albedo, clouds, constrained, gl]);

  useFrame((_, delta) => {
    const opacity = cloudMaterial.current?.uniforms.uOpacity;
    if (opacity && typeof opacity.value === "number") {
      opacity.value = THREE.MathUtils.damp(
        opacity.value,
        constrained ? 0.12 : 0.17,
        3,
        delta,
      );
    }
  });

  return (
    <>
      <mesh>
        <sphereGeometry
          args={[1.48, constrained ? 64 : 96, constrained ? 64 : 96]}
        />
        <meshStandardMaterial
          map={albedo}
          roughness={0.9}
          metalness={0.01}
          emissive="#07141a"
          emissiveIntensity={0.1}
        />
      </mesh>
      <mesh scale={1.006}>
        <sphereGeometry
          args={[1.48, constrained ? 48 : 72, constrained ? 48 : 72]}
        />
        <shaderMaterial
          ref={cloudMaterial}
          vertexShader={CLOUD_VERTEX_SHADER}
          fragmentShader={CLOUD_FRAGMENT_SHADER}
          uniforms={{ uClouds: { value: clouds }, uOpacity: { value: 0 } }}
          transparent
          depthWrite={false}
        />
      </mesh>
      <mesh scale={1.075}>
        <sphereGeometry
          args={[1.48, constrained ? 48 : 72, constrained ? 48 : 72]}
        />
        <shaderMaterial
          vertexShader={ATMOSPHERE_VERTEX_SHADER}
          fragmentShader={ATMOSPHERE_FRAGMENT_SHADER}
          uniforms={{ uColour: { value: new THREE.Color("#4ec9d0") } }}
          transparent
          side={THREE.BackSide}
          depthWrite={false}
        />
      </mesh>
    </>
  );
}

function BoundaryLayer({ constrained }: { constrained: boolean }) {
  const [document, setDocument] = useState<GeoJsonDocument | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(GLOBE_ASSETS.boundaries, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`BOUNDARY_ASSET_${response.status}`);
        return response.json() as Promise<GeoJsonDocument>;
      })
      .then(setDocument)
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError"))
          console.warn("AXIGNAL globe boundaries unavailable", error);
      });
    return () => controller.abort();
  }, []);

  const geometry = useMemo(
    () =>
      document ? createBoundaryGeometry(document, constrained ? 3 : 2) : null,
    [constrained, document],
  );
  useEffect(() => () => geometry?.dispose(), [geometry]);

  if (!geometry) return null;
  return (
    <lineSegments geometry={geometry}>
      <lineBasicMaterial
        color="#91e5df"
        transparent
        opacity={constrained ? 0.25 : 0.36}
        depthWrite={false}
      />
    </lineSegments>
  );
}

type MarkerLayout = {
  id: string;
  opportunities: Opportunity[];
  point: THREE.Vector3;
  orientation: THREE.Quaternion;
  isCluster: boolean;
};

function clusterMarkerLayouts(
  markers: Array<{ opportunity: Opportunity; point: THREE.Vector3 }>,
  zoomDistance: number,
): MarkerLayout[] {
  const zoomProgress = THREE.MathUtils.clamp(
    (6.2 - zoomDistance) / (6.2 - 2.7),
    0,
    1,
  );
  const clusterRadius = THREE.MathUtils.lerp(0.2, 0.045, zoomProgress);
  const expanded = zoomProgress > 0.72;
  const clusters: Array<{
    center: THREE.Vector3;
    markers: Array<{ opportunity: Opportunity; point: THREE.Vector3 }>;
  }> = [];

  for (const marker of markers) {
    const cluster = clusters.find(
      (candidate) => candidate.center.distanceTo(marker.point) <= clusterRadius,
    );
    if (!cluster) {
      clusters.push({ center: marker.point.clone(), markers: [marker] });
      continue;
    }
    cluster.markers.push(marker);
    cluster.center
      .multiplyScalar(cluster.markers.length - 1)
      .add(marker.point)
      .divideScalar(cluster.markers.length)
      .normalize()
      .multiplyScalar(1.51);
  }

  return clusters.flatMap<MarkerLayout>((cluster, clusterIndex): MarkerLayout[] => {
    const isCluster = cluster.markers.length > 1 && !expanded;
    if (isCluster) {
      return [{
        id: `cluster-${clusterIndex}-${cluster.markers.map((item) => item.opportunity.id).join("-")}`,
        opportunities: cluster.markers.map((item) => item.opportunity),
        point: cluster.center,
        orientation: surfaceOrientation(cluster.center),
        isCluster: true,
      }];
    }

    const spread = THREE.MathUtils.lerp(0.045, 0.1, zoomProgress);
    const normal = cluster.center.clone().normalize();
    let tangentA = new THREE.Vector3(0, 1, 0).cross(normal);
    if (tangentA.lengthSq() < 0.01) tangentA = new THREE.Vector3(1, 0, 0).cross(normal);
    tangentA.normalize();
    const tangentB = normal.clone().cross(tangentA).normalize();

    return cluster.markers.map((marker, markerIndex) => {
      const point = cluster.markers.length === 1
        ? marker.point
        : cluster.center.clone()
            .add(tangentA.clone().multiplyScalar(Math.cos((markerIndex / cluster.markers.length) * Math.PI * 2) * spread))
            .add(tangentB.clone().multiplyScalar(Math.sin((markerIndex / cluster.markers.length) * Math.PI * 2) * spread))
            .normalize()
            .multiplyScalar(1.51);
      return {
        id: marker.opportunity.id,
        opportunities: [marker.opportunity],
        point,
        orientation: surfaceOrientation(point),
        isCluster: false,
      };
    });
  });
}

function OpportunityMarkers({
  opportunities,
  selectedOpportunityId,
  label,
  rotation,
  onSelect,
}: Pick<GlobeSceneProps, "opportunities" | "selectedOpportunityId" | "label" | "rotation" | "onSelect">) {
  const pulseGroups = useRef<Array<THREE.Group | null>>([]);
  const { camera } = useThree();
  const zoomDistanceRef = useRef(camera.position.length());
  const [zoomDistance, setZoomDistance] = useState(camera.position.length());
  const markers = useMemo(
    () =>
      opportunities.map((opportunity) => {
        const point = latLonToVector(
          opportunity.latitude,
          opportunity.longitude,
        );
        return { opportunity, point };
      }),
    [opportunities],
  );
  const layouts = useMemo(
    () => clusterMarkerLayouts(markers, zoomDistance),
    [markers, zoomDistance],
  );

  useFrame(({ clock }) => {
    const pulse = 1 + Math.sin(clock.elapsedTime * 2.3) * 0.1;
    pulseGroups.current.forEach((group) => group?.scale.setScalar(pulse));
    const nextZoomDistance = Math.round(camera.position.length() * 10) / 10;
    if (Math.abs(nextZoomDistance - zoomDistanceRef.current) >= 0.1) {
      zoomDistanceRef.current = nextZoomDistance;
      setZoomDistance(nextZoomDistance);
    }
  });

  return (
    <>
      {layouts.map((layout, index) => {
        const selectedOpportunity = layout.opportunities.find((item) => item.id === selectedOpportunityId) ?? layout.opportunities[0]!;
        const isSelected = layout.opportunities.some((item) => item.id === selectedOpportunityId);
        const colour = semanticMarkerColour(selectedOpportunity);
        const markerSize = layout.isCluster ? (isSelected ? 0.064 : 0.052) : (isSelected ? 0.037 : 0.026);
        const cardOnLeft = layout.point
          .clone()
          .applyEuler(rotation)
          .project(camera).x > 0.35;
        return (
          <group
            key={layout.id}
            position={layout.point}
            quaternion={layout.orientation}
            onClick={(event) => {
              event.stopPropagation();
              onSelect(selectedOpportunity.id);
            }}
            onPointerOver={(event) => {
              event.stopPropagation();
            }}
            onPointerOut={(event) => {
              event.stopPropagation();
            }}
          >
            <mesh>
              <sphereGeometry args={[layout.isCluster ? 0.18 : 0.12, 12, 12]} />
              <meshBasicMaterial transparent opacity={0} depthWrite={false} />
            </mesh>
            {layout.isCluster ? (
              <Html position={[0, 0, 0.2]} center pointerEvents="none" zIndexRange={[15, 0]}>
                <span className={styles.globeClusterBadge} aria-label={`${layout.opportunities.length} opportunities in this area`}>
                  {layout.opportunities.length}
                </span>
              </Html>
            ) : null}
            {isSelected ? (
              <Html
                position={[0, 0, 0.16]}
                pointerEvents="none"
                zIndexRange={[20, 0]}
              >
                <div
                  className={`${styles.globeMarkerCard} ${cardOnLeft ? styles.globeMarkerCardLeft : ""}`}
                  role="status"
                >
                  <strong>{label}</strong>
                  <span>{opportunities.length} opportunities detected</span>
                  <span>
                    Selected <b>{selectedOpportunity.name}</b>
                  </span>
                  <span>
                    Evidence fit <b>{selectedOpportunity.expectedReturn ?? "Unknown"}</b>
                  </span>
                  <span>
                    Confidence <b>{selectedOpportunity.confidence === null ? "Unknown" : `${Math.round(selectedOpportunity.confidence * 100)}%`}</b>
                  </span>
                </div>
              </Html>
            ) : null}
            <mesh>
              <sphereGeometry args={[markerSize, 16, 16]} />
              <meshBasicMaterial color={colour} />
            </mesh>
            <group
              ref={(element) => {
                pulseGroups.current[index] = element;
              }}
            >
              <mesh>
                <ringGeometry
                  args={[
                    layout.isCluster ? (isSelected ? 0.078 : 0.064) : (isSelected ? 0.053 : 0.04),
                    layout.isCluster ? (isSelected ? 0.098 : 0.083) : (isSelected ? 0.068 : 0.052),
                    28,
                  ]}
                />
                <meshBasicMaterial
                  color={colour}
                  transparent
                  opacity={isSelected ? 0.94 : 0.58}
                  side={THREE.DoubleSide}
                  depthWrite={false}
                />
              </mesh>
            </group>
          </group>
        );
      })}
    </>
  );
}

function GlobeScene({
  opportunities,
  selectedOpportunityId,
  label,
  rotation,
  onContextFailure,
  onSelect,
}: GlobeSceneProps) {
  const constrained = useMemo(isConstrainedDevice, []);
  const { camera, gl } = useThree();
  const geographicNorth = useMemo(
    () => new THREE.Vector3(0, 1, 0).applyEuler(rotation).normalize(),
    [rotation],
  );

  useEffect(() => {
    // OrbitControls normally uses world Y as its up axis. The globe may be
    // initially focused on another longitude/latitude, so align the control
    // frame with the globe's geographic north to keep manual motion strictly
    // East-West and North-South, without a roll axis.
    camera.up.copy(geographicNorth);
    camera.lookAt(0, 0, 0);
  }, [camera, geographicNorth]);

  useEffect(() => {
    const canvas = gl.domElement;
    const onContextLost = (event: Event) => {
      event.preventDefault();
      onContextFailure();
    };
    canvas.addEventListener("webglcontextlost", onContextLost);
    return () => canvas.removeEventListener("webglcontextlost", onContextLost);
  }, [gl.domElement, onContextFailure]);

  return (
    <>
      <ambientLight intensity={0.72} />
      <directionalLight
        position={[3.2, 2.4, 4]}
        intensity={1.7}
        color="#efffff"
      />
      <pointLight position={[-3, -1, 2]} intensity={0.48} color="#00e1cf" />
      <OrbitControls
        makeDefault
        enablePan={false}
        enableRotate
        enableZoom
        enableDamping
        dampingFactor={0.08}
        screenSpacePanning={false}
        minAzimuthAngle={-Infinity}
        maxAzimuthAngle={Infinity}
        minDistance={2.7}
        maxDistance={6.2}
        minPolarAngle={0.42}
        maxPolarAngle={2.72}
        rotateSpeed={0.52}
        zoomSpeed={0.72}
        autoRotate={false}
      />
      <group rotation={rotation}>
        <EarthSurface constrained={constrained} />
        <BoundaryLayer constrained={constrained} />
        <OpportunityMarkers
          opportunities={opportunities}
          selectedOpportunityId={selectedOpportunityId}
          label={label}
          rotation={rotation}
          onSelect={onSelect}
        />
      </group>
    </>
  );
}

function hasWebGlSupport() {
  const canvas = document.createElement("canvas");
  const context =
    canvas.getContext("webgl2", { powerPreference: "high-performance" }) ??
    canvas.getContext("webgl", { powerPreference: "high-performance" });
  if (!context) return false;
  context.getExtension("WEBGL_lose_context")?.loseContext();
  return true;
}

class GlobeErrorBoundary extends Component<
  { children: ReactNode; onFailure: () => void },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("AXIGNAL Globe WebGL initialisation failed", error, info);
    this.props.onFailure();
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}

type SemanticGlobeProps = Pick<
  GlobeSceneProps,
  "opportunities" | "selectedOpportunityId"
> & {
  label: string;
  onSelect: (opportunityId: string) => void;
};

function sameOpportunitySet(
  previous: readonly Opportunity[],
  next: readonly Opportunity[],
) {
  if (previous === next) return true;
  if (previous.length !== next.length) return false;
  return previous.every((item, index) => {
    const candidate = next[index];
    return Boolean(
      candidate &&
        item.id === candidate.id &&
        item.name === candidate.name &&
        item.level === candidate.level &&
        item.expectedReturn === candidate.expectedReturn &&
        item.confidence === candidate.confidence &&
        item.latitude === candidate.latitude &&
        item.longitude === candidate.longitude,
    );
  });
}

function areGlobePropsEqual(
  previous: SemanticGlobeProps,
  next: SemanticGlobeProps,
) {
  return (
    previous.label === next.label &&
    previous.selectedOpportunityId === next.selectedOpportunityId &&
    sameOpportunitySet(previous.opportunities, next.opportunities)
  );
}

export const SemanticGlobe = memo(function SemanticGlobe({
  opportunities,
  selectedOpportunityId,
  label,
  onSelect,
}: SemanticGlobeProps) {
  const selected =
    opportunities.find((item) => item.id === selectedOpportunityId) ??
    opportunities[0];
  const rotation = useMemo(
    () => rotationForInvestigation(opportunities),
    [opportunities],
  );
  const [webglState, setWebglState] = useState<
    "checking" | "ready" | "unavailable"
  >("checking");

  useEffect(
    () => setWebglState(hasWebGlSupport() ? "ready" : "unavailable"),
    [],
  );
  const failWebGl = () => setWebglState("unavailable");

  return (
    <section
      className={styles.globeSurface}
      aria-label={label}
      aria-describedby="axignal-globe-description"
    >
      <p id="axignal-globe-description" className={styles.srOnly}>
        Cartographic globe centred on the current investigation. Country
        boundaries use the Natural Earth 1:50m regional dataset; opportunity
        markers are derived only from the current investigation context.
      </p>
      {webglState === "ready" ? (
        <GlobeErrorBoundary onFailure={failWebGl}>
          <Canvas
            className={styles.globeCanvas}
            aria-hidden="true"
            data-testid="semantic-globe-webgl"
            camera={{ position: [0, 0, 4.35], fov: 38, near: 0.1, far: 100 }}
            dpr={[1, 1.5]}
            gl={{
              antialias: true,
              alpha: true,
              powerPreference: "high-performance",
            }}
          >
            <Suspense fallback={null}>
              <GlobeScene
                opportunities={opportunities}
                selectedOpportunityId={selectedOpportunityId}
                label={label}
                rotation={rotation}
                onContextFailure={failWebGl}
                onSelect={onSelect}
              />
            </Suspense>
          </Canvas>
        </GlobeErrorBoundary>
      ) : (
        <div className={styles.globeFallback} role="status">
          <img src="/globe/globe-poster.webp" alt="" />
          <span>
            {webglState === "checking"
              ? "Preparing cartographic globe…"
              : "Cartographic globe unavailable. The accessible opportunity list remains available below."}
          </span>
        </div>
      )}
      {webglState !== "ready" && selected ? (
        <div className={styles.globeCallout}>
          <strong>{label}</strong>
          <span>{opportunities.length} opportunities detected</span>
          <span>
            Selected <b>{selected.name}</b>
          </span>
          <span>
            Evidence fit <b>{selected.expectedReturn ?? "Unknown"}</b>
          </span>
          <span>
            Confidence{" "}
            <b>
              {selected.confidence === null
                ? "Unknown"
                : `${Math.round(selected.confidence * 100)}%`}
            </b>
          </span>
        </div>
      ) : null}
      <div className={styles.legend} aria-hidden="true">
        <span>OPPORTUNITY POTENTIAL</span>
        <i />
        <div>
          <small>Very low</small>
          <small>Medium</small>
          <small>Very high</small>
          <small>No data</small>
        </div>
      </div>
      <small
        className={styles.globeAttribution}
        aria-label="Earth imagery: NASA Earth Observatory. Country boundaries: Natural Earth."
      >
        NASA Earth Observatory · Natural Earth
      </small>
      <table className={styles.srOnly}>
        <caption>{label}: accessible geographic opportunity list</caption>
        <thead>
          <tr>
            <th>Opportunity</th>
            <th>Latitude</th>
            <th>Longitude</th>
            <th>Evidence fit</th>
            <th>Confidence</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {opportunities.map((opportunity) => (
            <tr key={opportunity.id}>
              <th scope="row">{opportunity.name}</th>
              <td>{opportunity.latitude}</td>
              <td>{opportunity.longitude}</td>
              <td>{opportunity.expectedReturn ?? "Unknown"}</td>
              <td>{opportunity.confidence ?? "Unknown"}</td>
              <td>
                <button type="button" onClick={() => onSelect(opportunity.id)}>
                  Select {opportunity.name}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}, areGlobePropsEqual);
