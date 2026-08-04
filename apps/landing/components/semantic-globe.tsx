"use client";

import { OrbitControls, Stars, useTexture } from "@react-three/drei";
import {
  Canvas,
  type ThreeEvent,
  useFrame,
  useThree
} from "@react-three/fiber";
import {
  Component,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ErrorInfo,
  type ReactNode
} from "react";
import * as THREE from "three";
import { trackLandingEvent } from "@/lib/analytics";
import {
  EUROPE_LOD_BOUNDS,
  GLOBE_TIER_CONFIGS,
  createBoundaryGeometry,
  estimateTextureMemoryMb,
  latLonToVector,
  selectGlobeTextureTier,
  type GlobeRuntimeTelemetry,
  type GlobeTierConfig
} from "@/lib/globe-rendering";
import { sourcePoints, type SourcePoint, type SourceState } from "@/lib/landing-data";
import type { LandingMessages, Locale } from "@/lib/i18n";

declare global {
  interface Window {
    __AXIGNAL_GLOBE_RUNTIME__?: GlobeRuntimeTelemetry;
  }
}

type ProgressRef = { current: number };

type SemanticGlobeProps = {
  progressRef: ProgressRef;
  reducedMotion: boolean;
  lightTheme: boolean;
  locale: Locale;
  labels: LandingMessages["globe"];
};

type RuntimePatch = Partial<GlobeRuntimeTelemetry>;

const initialRuntime: GlobeRuntimeTelemetry = {
  textureTier: "pending",
  lodRequested: false,
  lodLoaded: false,
  lodActive: false,
  lodLoadMs: null,
  lodFailure: null,
  lodFallback: "NONE",
  boundaryLayer: "PENDING",
  boundaryLodRequested: false,
  boundaryLodLoaded: false,
  boundaryLodActive: false,
  boundaryLodFailure: null,
  effectiveDpr: 1,
  drawingBufferWidth: 0,
  drawingBufferHeight: 0,
  averageFps: null,
  p95FrameTimeMs: null,
  estimatedTextureMemoryMb: 0,
  webglErrors: 0,
  renderer: "PENDING",
  maxTextureSize: 0,
  maxAnisotropy: 0,
  contextState: "CHECKING"
};

const markerColours: Record<SourceState, string> = {
  ADMITTED: "#00e1cf",
  TECHNICAL_PROBE: "#f5b942",
  DISCOVERED: "#829399",
  CANDIDATE: "#8d6cff",
  BLOCKED: "#ff5b52",
  RIGHTS_REVIEW: "#f5b942",
  UNAVAILABLE: "#4d5960"
};

const europeanOpportunities = [
  { id: "madrid", latitude: 40.4168, longitude: -3.7038 },
  { id: "lisbon", latitude: 38.7223, longitude: -9.1393 },
  { id: "london", latitude: 51.5074, longitude: -0.1278 },
  { id: "dublin", latitude: 53.3498, longitude: -6.2603 },
  { id: "paris", latitude: 48.8566, longitude: 2.3522 },
  { id: "amsterdam", latitude: 52.3676, longitude: 4.9041 },
  { id: "copenhagen", latitude: 55.6761, longitude: 12.5683 },
  { id: "stockholm", latitude: 59.3293, longitude: 18.0686 },
  { id: "oslo", latitude: 59.9139, longitude: 10.7522 },
  { id: "helsinki", latitude: 60.1699, longitude: 24.9384 },
  { id: "tallinn", latitude: 59.437, longitude: 24.7536 },
  { id: "riga", latitude: 56.9496, longitude: 24.1052 },
  { id: "vilnius", latitude: 54.6872, longitude: 25.2797 },
  { id: "berlin", latitude: 52.52, longitude: 13.405 },
  { id: "brussels", latitude: 50.8503, longitude: 4.3517 },
  { id: "zurich", latitude: 47.3769, longitude: 8.5417 },
  { id: "vienna", latitude: 48.2082, longitude: 16.3738 },
  { id: "prague", latitude: 50.0755, longitude: 14.4378 },
  { id: "warsaw", latitude: 52.2297, longitude: 21.0122 },
  { id: "budapest", latitude: 47.4979, longitude: 19.0402 },
  { id: "zagreb", latitude: 45.815, longitude: 15.9819 },
  { id: "belgrade", latitude: 44.7866, longitude: 20.4489 },
  { id: "sofia", latitude: 42.6977, longitude: 23.3219 },
  { id: "rome", latitude: 41.9028, longitude: 12.4964 },
  { id: "milan", latitude: 45.4642, longitude: 9.19 },
  { id: "bucharest", latitude: 44.4268, longitude: 26.1025 },
  { id: "athens", latitude: 37.9838, longitude: 23.7275 }
] as const;

function smoothRange(value: number, from: number, to: number) {
  return THREE.MathUtils.smoothstep(value, from, to);
}

function configureColourTexture(
  texture: THREE.Texture,
  renderer: THREE.WebGLRenderer,
  requestedAnisotropy: number
) {
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = Math.min(requestedAnisotropy, renderer.capabilities.getMaxAnisotropy());
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.generateMipmaps = true;
  texture.needsUpdate = true;
}

type PositionedSource = {
  source: SourcePoint;
  point: THREE.Vector3;
};

function SourceMarkerLayer({
  markers,
  onSelect
}: {
  markers: PositionedSource[];
  onSelect: (source: SourcePoint) => void;
}) {
  const mesh = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  useEffect(() => {
    if (!mesh.current) return;
    markers.forEach(({ source, point }, index) => {
      dummy.position.copy(point);
      dummy.scale.setScalar(source.state === "ADMITTED" ? 1 : 0.72);
      dummy.updateMatrix();
      mesh.current?.setMatrixAt(index, dummy.matrix);
      mesh.current?.setColorAt(index, new THREE.Color(markerColours[source.state]));
    });
    mesh.current.instanceMatrix.needsUpdate = true;
    if (mesh.current.instanceColor) mesh.current.instanceColor.needsUpdate = true;
  }, [dummy, markers]);

  return (
    <>
      <instancedMesh
        ref={mesh}
        args={[undefined, undefined, markers.length]}
        onClick={(event: ThreeEvent<MouseEvent>) => {
          event.stopPropagation();
          if (event.instanceId === undefined) return;
          const source = markers[event.instanceId]?.source;
          if (source) onSelect(source);
        }}
        onPointerEnter={() => {
          document.body.style.cursor = "pointer";
        }}
        onPointerLeave={() => {
          document.body.style.cursor = "";
        }}
      >
        <sphereGeometry args={[0.02, 16, 16]} />
        <meshBasicMaterial />
      </instancedMesh>
    </>
  );
}

type PositionedOpportunity = {
  id: string;
  point: THREE.Vector3;
};

function OpportunityMarkerLayer({
  markers,
  progressRef
}: {
  markers: PositionedOpportunity[];
  progressRef: ProgressRef;
}) {
  const mesh = useRef<THREE.InstancedMesh>(null);
  const material = useRef<THREE.MeshBasicMaterial>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  useFrame(() => {
    const reveal =
      smoothRange(progressRef.current, 0.12, 0.3) *
      (1 - smoothRange(progressRef.current, 0.58, 0.76) * 0.72);
    markers.forEach((marker, index) => {
      dummy.position.copy(marker.point);
      dummy.scale.setScalar(0.001 + reveal * 0.82);
      dummy.updateMatrix();
      mesh.current?.setMatrixAt(index, dummy.matrix);
    });
    if (mesh.current) mesh.current.instanceMatrix.needsUpdate = true;
    if (material.current) material.current.opacity = reveal * 0.9;
  });

  return (
    <>
      <instancedMesh ref={mesh} args={[undefined, undefined, markers.length]}>
        <sphereGeometry args={[0.012, 12, 12]} />
        <meshBasicMaterial ref={material} color="#e7f2f1" transparent opacity={0} />
      </instancedMesh>
    </>
  );
}

type CompiledGlobeShader = {
  uniforms: Record<string, { value: unknown }>;
  fragmentShader: string;
};

function EarthSurface({
  config,
  progressRef,
  lightTheme,
  onRuntime
}: {
  config: GlobeTierConfig;
  progressRef: ProgressRef;
  lightTheme: boolean;
  onRuntime: (patch: RuntimePatch) => void;
}) {
  const { gl } = useThree();
  const globalTexture = useTexture(config.globalAsset);
  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        map: globalTexture,
        roughness: 0.88,
        metalness: 0.02,
        emissive: new THREE.Color("#020a0d"),
        emissiveIntensity: 0.16
      }),
    [globalTexture]
  );
  const placeholder = useMemo(() => {
    const texture = new THREE.DataTexture(new Uint8Array([16, 22, 24, 255]), 1, 1);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.needsUpdate = true;
    return texture;
  }, []);
  const shader = useRef<CompiledGlobeShader | null>(null);
  const regionalTexture = useRef<THREE.Texture>(placeholder);
  const requested = useRef(false);
  const loaded = useRef(false);
  const active = useRef(false);
  const requestedAt = useRef(0);
  const [loadRegional, setLoadRegional] = useState(false);

  useEffect(() => {
    configureColourTexture(globalTexture, gl, config.albedoAnisotropy);
  }, [config.albedoAnisotropy, gl, globalTexture]);

  useEffect(() => {
    material.emissive.set(lightTheme ? "#9ddbd4" : "#020a0d");
    material.emissiveIntensity = lightTheme ? 0.28 : 0.16;
  }, [lightTheme, material]);

  useEffect(() => {
    material.onBeforeCompile = (compiled) => {
      compiled.uniforms.axRegionalMap = { value: regionalTexture.current };
      compiled.uniforms.axRegionalMix = { value: 0 };
      compiled.uniforms.axRegionalBounds = { value: EUROPE_LOD_BOUNDS };
      compiled.fragmentShader = compiled.fragmentShader
        .replace(
          "#include <map_pars_fragment>",
          `#include <map_pars_fragment>
uniform sampler2D axRegionalMap;
uniform float axRegionalMix;
uniform vec4 axRegionalBounds;`
        )
        .replace(
          "#include <map_fragment>",
          `#include <map_fragment>
#ifdef USE_MAP
  vec2 axRegionalSize = axRegionalBounds.zw - axRegionalBounds.xy;
  vec2 axRegionalUv = (vMapUv - axRegionalBounds.xy) / axRegionalSize;
  vec2 axEdge = min(axRegionalUv, vec2(1.0) - axRegionalUv);
  float axInside = step(0.0, axEdge.x) * step(0.0, axEdge.y);
  float axFeather = smoothstep(0.0, 0.065, min(axEdge.x, axEdge.y)) * axInside;
  vec4 axRegionalTexel = texture2D(axRegionalMap, clamp(axRegionalUv, 0.0, 1.0));
  diffuseColor.rgb = mix(
    diffuseColor.rgb,
    axRegionalTexel.rgb,
    clamp(axRegionalMix * axFeather, 0.0, 1.0)
  );
#endif`
        );
      shader.current = compiled as CompiledGlobeShader;
    };
    material.customProgramCacheKey = () => "axignal-europe-regional-lod-v1";
    material.needsUpdate = true;
    return () => {
      shader.current = null;
      material.dispose();
    };
  }, [material]);

  useEffect(() => {
    if (!loadRegional) return;
    let cancelled = false;
    const loader = new THREE.TextureLoader();
    loader.load(
      config.regionalAsset,
      (texture) => {
        if (cancelled) {
          texture.dispose();
          return;
        }
        configureColourTexture(texture, gl, config.albedoAnisotropy);
        regionalTexture.current = texture;
        loaded.current = true;
        if (shader.current?.uniforms.axRegionalMap) {
          shader.current.uniforms.axRegionalMap.value = texture;
        }
        onRuntime({
          lodLoaded: true,
          lodLoadMs: Math.round(performance.now() - requestedAt.current),
          lodFailure: null,
          lodFallback: "NONE",
          estimatedTextureMemoryMb: estimateTextureMemoryMb(config, {
            regionalLoaded: true,
            cloudsEnabled: true
          })
        });
      },
      undefined,
      (error) => {
        if (cancelled) return;
        const message = error instanceof Error ? error.message : "REGIONAL_TEXTURE_LOAD_FAILED";
        onRuntime({
          lodLoaded: false,
          lodActive: false,
          lodFailure: message,
          lodFallback: "GLOBAL_TEXTURE"
        });
      }
    );

    return () => {
      cancelled = true;
      if (regionalTexture.current !== placeholder) {
        regionalTexture.current.dispose();
        regionalTexture.current = placeholder;
      }
    };
  }, [
    config,
    config.albedoAnisotropy,
    config.regionalAsset,
    gl,
    loadRegional,
    onRuntime,
    placeholder
  ]);

  useEffect(() => () => placeholder.dispose(), [placeholder]);

  useFrame((_, delta) => {
    const progress = THREE.MathUtils.clamp(progressRef.current, 0, 1);
    if (progress >= 0.055 && !requested.current) {
      requested.current = true;
      requestedAt.current = performance.now();
      onRuntime({ lodRequested: true });
      setLoadRegional(true);
    }

    const target = loaded.current ? smoothRange(progress, 0.1, 0.3) : 0;
    const uniform = shader.current?.uniforms.axRegionalMix;
    if (uniform) {
      const current = typeof uniform.value === "number" ? uniform.value : 0;
      uniform.value = THREE.MathUtils.damp(current, target, 7, delta);
      const nextActive = (uniform.value as number) >= 0.55;
      if (nextActive !== active.current) {
        active.current = nextActive;
        onRuntime({ lodActive: nextActive });
      }
    }
  });

  return (
    <mesh>
      <sphereGeometry args={[1.48, 128, 128]} />
      <primitive object={material} attach="material" />
    </mesh>
  );
}

function BoundaryLayer({
  config,
  progressRef,
  onRuntime
}: {
  config: GlobeTierConfig;
  progressRef: ProgressRef;
  onRuntime: (patch: RuntimePatch) => void;
}) {
  const globalMaterial = useRef<THREE.LineBasicMaterial>(null);
  const regionalMaterial = useRef<THREE.LineBasicMaterial>(null);
  const [globalGeometry, setGlobalGeometry] = useState<THREE.BufferGeometry | null>(null);
  const [regionalGeometry, setRegionalGeometry] =
    useState<THREE.BufferGeometry | null>(null);
  const [loadRegional, setLoadRegional] = useState(false);
  const regionalRequested = useRef(false);
  const regionalLoaded = useRef(false);
  const regionalActive = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/globe/countries-110m.simplified.geojson", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`BOUNDARY_HTTP_${response.status}`);
        return response.json();
      })
      .then((document: unknown) => {
        const next = createBoundaryGeometry(
          document as Parameters<typeof createBoundaryGeometry>[0],
          config.boundaryStride
        );
        setGlobalGeometry(next);
        onRuntime({ boundaryLayer: "ACTIVE" });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        console.error("AXIGNAL Globe boundary layer failed", error);
        onRuntime({ boundaryLayer: "FAILED" });
      });
    return () => controller.abort();
  }, [config.boundaryStride, onRuntime]);

  useEffect(() => {
    if (!loadRegional || config.id === "mobile") return;
    const controller = new AbortController();
    fetch("/globe/europe-boundaries-50m.geojson", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`BOUNDARY_LOD_HTTP_${response.status}`);
        return response.json();
      })
      .then((document: unknown) => {
        const next = createBoundaryGeometry(
          document as Parameters<typeof createBoundaryGeometry>[0],
          1
        );
        regionalLoaded.current = true;
        setRegionalGeometry(next);
        onRuntime({ boundaryLodLoaded: true, boundaryLodFailure: null });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message =
          error instanceof Error ? error.message : "BOUNDARY_LOD_LOAD_FAILED";
        console.error("AXIGNAL Globe regional boundary layer failed", error);
        onRuntime({
          boundaryLodLoaded: false,
          boundaryLodActive: false,
          boundaryLodFailure: message
        });
      });
    return () => controller.abort();
  }, [config.id, loadRegional, onRuntime]);

  useEffect(() => () => globalGeometry?.dispose(), [globalGeometry]);
  useEffect(() => () => regionalGeometry?.dispose(), [regionalGeometry]);

  useFrame(() => {
    const progress = progressRef.current;
    const europe = smoothRange(progress, 0.1, 0.3);
    const supportsRegional = config.id !== "mobile";
    if (supportsRegional && progress >= 0.055 && !regionalRequested.current) {
      regionalRequested.current = true;
      setLoadRegional(true);
      onRuntime({ boundaryLodRequested: true });
    }

    const regionalMix = supportsRegional && regionalLoaded.current ? europe : 0;
    if (globalMaterial.current) {
      globalMaterial.current.opacity = supportsRegional
        ? THREE.MathUtils.lerp(0.16, 0.055, regionalMix)
        : 0.16 + europe * 0.42;
    }
    if (regionalMaterial.current) {
      regionalMaterial.current.opacity = regionalMix * 0.62;
    }

    const nextActive = regionalMix >= 0.55;
    if (nextActive !== regionalActive.current) {
      regionalActive.current = nextActive;
      onRuntime({ boundaryLodActive: nextActive });
    }
  });

  return (
    <>
      {globalGeometry ? (
        <lineSegments geometry={globalGeometry} renderOrder={3}>
          <lineBasicMaterial
            ref={globalMaterial}
            color="#00e1cf"
            transparent
            opacity={0.16}
            depthWrite={false}
            toneMapped={false}
          />
        </lineSegments>
      ) : null}
      {regionalGeometry ? (
        <lineSegments geometry={regionalGeometry} renderOrder={4}>
          <lineBasicMaterial
            ref={regionalMaterial}
            color="#00e1cf"
            transparent
            opacity={0}
            depthWrite={false}
            toneMapped={false}
          />
        </lineSegments>
      ) : null}
    </>
  );
}

function CloudLayer({
  config,
  progressRef,
  reducedMotion,
  performancePressure
}: {
  config: GlobeTierConfig;
  progressRef: ProgressRef;
  reducedMotion: boolean;
  performancePressure: boolean;
}) {
  const clouds = useRef<THREE.Mesh>(null);
  const material = useRef<THREE.MeshPhongMaterial>(null);
  const texture = useTexture(config.cloudAsset);
  const { gl } = useThree();

  useEffect(() => {
    configureColourTexture(texture, gl, config.cloudAnisotropy);
  }, [config.cloudAnisotropy, gl, texture]);

  useFrame((_, delta) => {
    if (clouds.current && !reducedMotion) {
      clouds.current.rotation.y -= delta * 0.0054;
    }
    if (!material.current) return;
    const investigation = smoothRange(progressRef.current, 0.48, 0.78);
    const dossier = smoothRange(progressRef.current, 0.78, 0.98);
    const baseOpacity = config.id === "mobile" ? 0.3 : 0.36;
    const pressureOpacity = performancePressure ? (config.id === "mobile" ? 0 : 0.2) : 1;
    material.current.opacity =
      Math.max(0, baseOpacity - investigation * 0.1 - dossier * 0.08) * pressureOpacity;
    material.current.visible = material.current.opacity > 0.01;
  });

  return (
    <mesh ref={clouds} scale={1.006} renderOrder={2}>
      <sphereGeometry args={[1.48, config.id === "mobile" ? 64 : 96, config.id === "mobile" ? 64 : 96]} />
      <meshPhongMaterial
        ref={material}
        map={texture}
        color="#c7d9dc"
        transparent
        opacity={0.36}
        shininess={4}
        depthWrite={false}
      />
    </mesh>
  );
}

function AtmosphereLayer({ progressRef }: { progressRef: ProgressRef }) {
  const material = useMemo(
    () =>
      new THREE.ShaderMaterial({
        transparent: true,
        side: THREE.BackSide,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: {
          uColour: { value: new THREE.Color("#74f0e5") },
          uIntensity: { value: 0.22 }
        },
        vertexShader: `
          varying vec3 vNormalView;
          varying vec3 vViewDirection;
          void main() {
            vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
            vNormalView = normalize(normalMatrix * normal);
            vViewDirection = normalize(-viewPosition.xyz);
            gl_Position = projectionMatrix * viewPosition;
          }
        `,
        fragmentShader: `
          uniform vec3 uColour;
          uniform float uIntensity;
          varying vec3 vNormalView;
          varying vec3 vViewDirection;
          void main() {
            float fresnel = pow(1.0 - abs(dot(vNormalView, vViewDirection)), 2.45);
            gl_FragColor = vec4(uColour, fresnel * uIntensity);
          }
        `
      }),
    []
  );

  useFrame(() => {
    const europe = smoothRange(progressRef.current, 0.1, 0.3);
    const dossier = smoothRange(progressRef.current, 0.8, 0.98);
    material.uniforms.uIntensity!.value = 0.18 + europe * 0.11 - dossier * 0.04;
  });

  useEffect(() => () => material.dispose(), [material]);

  return (
    <mesh scale={1.026}>
      <sphereGeometry args={[1.48, 72, 72]} />
      <primitive object={material} attach="material" />
    </mesh>
  );
}

function AdaptiveRenderer({
  config,
  onRuntime,
  onPerformancePressure,
  onContextFailure
}: {
  config: GlobeTierConfig;
  onRuntime: (patch: RuntimePatch) => void;
  onPerformancePressure: (pressure: boolean) => void;
  onContextFailure: () => void;
}) {
  const { gl, size, setDpr, setFrameloop, setSize, invalidate } = useThree();
  const samples = useRef(new Float32Array(240));
  const sampleCount = useRef(0);
  const sampleCursor = useRef(0);
  const elapsed = useRef(0);
  const lowWindows = useRef(0);
  const recoveryWindows = useRef(0);
  const targetDpr = useRef(1);
  const currentDpr = useRef(1);
  const pressureState = useRef(false);

  useEffect(() => {
    const desired = Math.max(1, Math.min(window.devicePixelRatio || 1, config.maxDpr));
    targetDpr.current = desired;
    currentDpr.current = desired;
    setDpr(desired);
    gl.setPixelRatio(desired);

    const context = gl.getContext();
    const debugInfo = context.getExtension("WEBGL_debug_renderer_info");
    const renderer = debugInfo
      ? String(context.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL))
      : String(context.getParameter(context.RENDERER));
    onRuntime({
      textureTier: config.id,
      renderer,
      maxTextureSize: gl.capabilities.maxTextureSize,
      maxAnisotropy: gl.capabilities.getMaxAnisotropy(),
      estimatedTextureMemoryMb: estimateTextureMemoryMb(config, {
        regionalLoaded: false,
        cloudsEnabled: true
      })
    });
  }, [config, gl, onRuntime, setDpr]);

  useEffect(() => {
    const container = gl.domElement.closest<HTMLElement>(".globe-canvas");
    if (!container) return;

    const resize = () => {
      const rect = container.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return;
      setSize(rect.width, rect.height, rect.top, rect.left);
      gl.setPixelRatio(currentDpr.current);
      gl.setSize(rect.width, rect.height, false);
      invalidate();
      window.requestAnimationFrame(() => {
        gl.setPixelRatio(currentDpr.current);
        gl.setSize(rect.width, rect.height, false);
        const effectiveDpr = gl.domElement.width / Math.max(1, rect.width);
        onRuntime({
          effectiveDpr: Number(effectiveDpr.toFixed(3)),
          drawingBufferWidth: gl.domElement.width,
          drawingBufferHeight: gl.domElement.height
        });
      });
    };
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(container);
    window.addEventListener("resize", resize);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", resize);
    };
  }, [gl, invalidate, onRuntime, setSize]);

  useEffect(() => {
    const target = gl.domElement.closest<HTMLElement>(".semantic-globe");
    if (!target) return;

    const isInViewport = () => {
      const rect = target.getBoundingClientRect();
      return (
        rect.bottom > 0 &&
        rect.top < window.innerHeight &&
        rect.right > 0 &&
        rect.left < window.innerWidth
      );
    };
    const updateVisibility = (visible: boolean) => {
      setFrameloop(visible && !document.hidden ? "always" : "never");
      if (visible && !document.hidden) invalidate();
    };
    const observer = new IntersectionObserver(
      ([entry]) => updateVisibility(Boolean(entry?.isIntersecting) || isInViewport()),
      { threshold: 0.01 }
    );
    const onVisibility = () => updateVisibility(isInViewport());
    onVisibility();
    observer.observe(target);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      observer.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
      setFrameloop("always");
    };
  }, [gl, invalidate, setFrameloop]);

  useEffect(() => {
    const canvas = gl.domElement;
    const onLost = (event: Event) => {
      event.preventDefault();
      onRuntime({ contextState: "FAILED", webglErrors: 1 });
      onContextFailure();
    };
    canvas.addEventListener("webglcontextlost", onLost);
    return () => canvas.removeEventListener("webglcontextlost", onLost);
  }, [gl, onContextFailure, onRuntime]);

  useFrame((_, delta) => {
    if (delta <= 0) return;
    samples.current[sampleCursor.current] = Math.min(delta * 1000, 1000);
    sampleCursor.current = (sampleCursor.current + 1) % samples.current.length;
    sampleCount.current = Math.min(samples.current.length, sampleCount.current + 1);
    elapsed.current += delta;
    if (elapsed.current < 2 || sampleCount.current < 8) return;
    elapsed.current = 0;

    const values = Array.from(samples.current.slice(0, sampleCount.current));
    const averageFrameTime = values.reduce((sum, value) => sum + value, 0) / values.length;
    const sorted = [...values].sort((a, b) => a - b);
    const p95 = sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * 0.95))] ?? 0;
    const fps = 1000 / averageFrameTime;
    const targetFps = config.id === "mobile" ? 30 : 55;

    if (fps < targetFps * 0.82 || p95 > (config.id === "mobile" ? 42 : 28)) {
      lowWindows.current += 1;
      recoveryWindows.current = 0;
    } else if (fps >= targetFps && p95 <= (config.id === "mobile" ? 34 : 22)) {
      recoveryWindows.current += 1;
      lowWindows.current = 0;
    } else {
      lowWindows.current = 0;
      recoveryWindows.current = 0;
    }

    if (lowWindows.current >= 2 && currentDpr.current > 1) {
      currentDpr.current = Math.max(1, currentDpr.current - 0.25);
      setDpr(currentDpr.current);
      gl.setPixelRatio(currentDpr.current);
      gl.setSize(size.width, size.height, false);
      invalidate();
      window.requestAnimationFrame(() => {
        onRuntime({
          effectiveDpr: Number(
            (gl.domElement.width / Math.max(1, size.width)).toFixed(3)
          ),
          drawingBufferWidth: gl.domElement.width,
          drawingBufferHeight: gl.domElement.height
        });
      });
      lowWindows.current = 0;
    } else if (
      recoveryWindows.current >= 3 &&
      currentDpr.current < targetDpr.current
    ) {
      currentDpr.current = Math.min(targetDpr.current, currentDpr.current + 0.125);
      setDpr(currentDpr.current);
      gl.setPixelRatio(currentDpr.current);
      gl.setSize(size.width, size.height, false);
      invalidate();
      window.requestAnimationFrame(() => {
        onRuntime({
          effectiveDpr: Number(
            (gl.domElement.width / Math.max(1, size.width)).toFixed(3)
          ),
          drawingBufferWidth: gl.domElement.width,
          drawingBufferHeight: gl.domElement.height
        });
      });
      recoveryWindows.current = 0;
    }

    const pressure = currentDpr.current < targetDpr.current - 0.1 || fps < targetFps * 0.86;
    if (pressure !== pressureState.current) {
      pressureState.current = pressure;
      onPerformancePressure(pressure);
    }

    const effectiveDpr =
      size.width > 0 ? gl.domElement.width / Math.max(1, size.width) : currentDpr.current;
    onRuntime({
      effectiveDpr: Number(effectiveDpr.toFixed(3)),
      drawingBufferWidth: gl.domElement.width,
      drawingBufferHeight: gl.domElement.height,
      averageFps: Number(fps.toFixed(1)),
      p95FrameTimeMs: Number(p95.toFixed(2))
    });
  });

  return null;
}

function GlobeScene({
  progressRef,
  reducedMotion,
  lightTheme,
  onSelect,
  onRuntime,
  onContextFailure
}: {
  progressRef: ProgressRef;
  reducedMotion: boolean;
  lightTheme: boolean;
  onSelect: (source: SourcePoint) => void;
  onRuntime: (patch: RuntimePatch) => void;
  onContextFailure: () => void;
}) {
  const globe = useRef<THREE.Group>(null);
  const keyLight = useRef<THREE.DirectionalLight>(null);
  const fillLight = useRef<THREE.PointLight>(null);
  const { camera, gl } = useThree();
  const [performancePressure, setPerformancePressure] = useState(false);
  const config = useMemo(() => {
    const memory =
      (navigator as Navigator & { deviceMemory?: number }).deviceMemory ?? 8;
    const tier = selectGlobeTextureTier({
      viewportWidth: window.innerWidth,
      devicePixelRatio: window.devicePixelRatio || 1,
      deviceMemory: memory,
      maxTextureSize: gl.capabilities.maxTextureSize,
      webgl2: gl.capabilities.isWebGL2,
      reducedMotion
    });
    return GLOBE_TIER_CONFIGS[tier];
  }, [gl, reducedMotion]);
  const sourceMarkers = useMemo(
    () =>
      sourcePoints.map((source) => {
        const point = latLonToVector(source.latitude, source.longitude);
        return { source, point };
      }),
    []
  );
  const opportunityMarkers = useMemo(
    () =>
      europeanOpportunities.map((opportunity) => {
        const point = latLonToVector(opportunity.latitude, opportunity.longitude, 1.525);
        return { ...opportunity, point };
      }),
    []
  );

  useFrame((state, delta) => {
    if (!globe.current) return;

    const progress = THREE.MathUtils.clamp(progressRef.current, 0, 1);
    const europe = smoothRange(progress, 0.1, 0.3);
    const fragmentation = smoothRange(progress, 0.3, 0.5);
    const investigation = smoothRange(progress, 0.58, 0.8);
    const dossier = smoothRange(progress, 0.8, 0.98);

    const targetX =
      THREE.MathUtils.lerp(0.78, 0.18, europe) - fragmentation * 0.62 - dossier * 0.38;
    const targetScale =
      THREE.MathUtils.lerp(1, 1.2, europe) -
      fragmentation * 0.25 -
      investigation * 0.14 -
      dossier * 0.14;
    globe.current.position.x = THREE.MathUtils.damp(
      globe.current.position.x,
      targetX,
      5,
      delta
    );
    globe.current.position.y = THREE.MathUtils.damp(
      globe.current.position.y,
      THREE.MathUtils.lerp(-0.05, -1.1, europe) + dossier * 0.14,
      5,
      delta
    );
    globe.current.scale.setScalar(
      THREE.MathUtils.damp(globe.current.scale.x, targetScale, 5, delta)
    );

    const targetRotationY = THREE.MathUtils.lerp(-0.34, -1.72, europe) + investigation * 0.05;
    globe.current.rotation.y = THREE.MathUtils.damp(
      globe.current.rotation.y,
      targetRotationY,
      5,
      delta
    );
    globe.current.rotation.x = THREE.MathUtils.damp(
      globe.current.rotation.x,
      THREE.MathUtils.lerp(-0.08, 0.26, europe),
      5,
      delta
    );

    if (!reducedMotion && progress < 0.08) {
      globe.current.rotation.y += delta * 0.018;
    }

    const cameraZ =
      THREE.MathUtils.lerp(4.65, 3.65, europe) + fragmentation * 0.28 + dossier * 0.3;
    camera.position.z = THREE.MathUtils.damp(camera.position.z, cameraZ, 5, delta);
    camera.position.x = THREE.MathUtils.damp(
      camera.position.x,
      investigation * 0.12,
      5,
      delta
    );
    camera.lookAt(0, 0, 0);

    if (keyLight.current) {
      keyLight.current.intensity = 2.15 + europe * 1.05 - dossier * 0.35 + (lightTheme ? 0.55 : 0);
      keyLight.current.position.x = 3 - investigation * 2;
    }
    if (fillLight.current) {
      fillLight.current.intensity = 1.05 + investigation * 1.25 + (lightTheme ? 0.35 : 0);
    }
    state.gl.setClearColor("#000000", 0);
  });

  return (
    <>
      <AdaptiveRenderer
        config={config}
        onRuntime={onRuntime}
        onPerformancePressure={setPerformancePressure}
        onContextFailure={onContextFailure}
      />
      <ambientLight intensity={lightTheme ? 0.72 : 0.46} />
      <directionalLight ref={keyLight} position={[3, 2.4, 4]} intensity={2.15} color="#f5fcff" />
      <pointLight ref={fillLight} position={[-3, -1.5, 2]} intensity={1.05} color="#00e1cf" />
      <Stars
        radius={28}
        depth={32}
        count={reducedMotion ? 220 : config.id === "mobile" ? 420 : 720}
        factor={1.2}
        saturation={0}
        fade
      />

      <group ref={globe} position={[0.78, -0.05, 0]} rotation={[-0.08, -0.34, 0.025]}>
        <EarthSurface
          config={config}
          progressRef={progressRef}
          lightTheme={lightTheme}
          onRuntime={onRuntime}
        />
        <AtmosphereLayer progressRef={progressRef} />
        <BoundaryLayer config={config} progressRef={progressRef} onRuntime={onRuntime} />
        <CloudLayer
          config={config}
          progressRef={progressRef}
          reducedMotion={reducedMotion}
          performancePressure={performancePressure}
        />
        <SourceMarkerLayer
          markers={sourceMarkers}
          onSelect={onSelect}
        />
        <OpportunityMarkerLayer
          markers={opportunityMarkers}
          progressRef={progressRef}
        />
      </group>

      <OrbitControls
        makeDefault
        enablePan={false}
        enableZoom
        enableRotate
        enableDamping={!reducedMotion}
        dampingFactor={0.06}
        minDistance={3.4}
        maxDistance={5.8}
        minPolarAngle={0.55}
        maxPolarAngle={2.5}
        autoRotate={false}
      />
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

export function SemanticGlobe({
  progressRef,
  reducedMotion,
  lightTheme,
  locale,
  labels
}: SemanticGlobeProps) {
  const [selected, setSelected] = useState<SourcePoint>(
    sourcePoints.find((source) => source.id === "EU_TED") ?? sourcePoints[0]!
  );
  const [webglState, setWebglState] = useState<
    "CHECKING" | "SUPPORTED" | "READY" | "FAILED" | "UNSUPPORTED"
  >("CHECKING");
  const [runtime, setRuntime] = useState<GlobeRuntimeTelemetry>(initialRuntime);

  const updateRuntime = useCallback((patch: RuntimePatch) => {
    setRuntime((current) => {
      const next = { ...current, ...patch };
      window.__AXIGNAL_GLOBE_RUNTIME__ = next;
      return next;
    });
  }, []);

  useEffect(() => {
    const supported = hasWebGlSupport();
    setWebglState(supported ? "SUPPORTED" : "UNSUPPORTED");
    updateRuntime({ contextState: supported ? "CHECKING" : "UNSUPPORTED" });
  }, [updateRuntime]);

  useEffect(
    () => () => {
      delete window.__AXIGNAL_GLOBE_RUNTIME__;
    },
    []
  );

  const selectSource = (source: SourcePoint) => {
    setSelected(source);
    trackLandingEvent("globe_source_select", { locale, source_state: source.state });
  };

  const failWebGl = useCallback(() => {
    setWebglState("FAILED");
    updateRuntime({ contextState: "FAILED", lodFallback: "GLOBAL_TEXTURE" });
  }, [updateRuntime]);

  const showPoster = webglState === "FAILED" || webglState === "UNSUPPORTED";

  return (
    <div
      className="semantic-globe cinematic-globe"
      data-testid="semantic-globe"
      data-texture-tier={runtime.textureTier}
      data-lod-requested={String(runtime.lodRequested)}
      data-lod-loaded={String(runtime.lodLoaded)}
      data-lod-active={String(runtime.lodActive)}
      data-lod-load-ms={runtime.lodLoadMs ?? "NOT_LOADED"}
      data-lod-fallback={runtime.lodFallback}
      data-boundary-layer={runtime.boundaryLayer}
      data-boundary-lod-requested={String(runtime.boundaryLodRequested)}
      data-boundary-lod-loaded={String(runtime.boundaryLodLoaded)}
      data-boundary-lod-active={String(runtime.boundaryLodActive)}
      data-boundary-lod-failure={runtime.boundaryLodFailure ?? "NONE"}
      data-effective-dpr={runtime.effectiveDpr}
      data-drawing-buffer={`${runtime.drawingBufferWidth}x${runtime.drawingBufferHeight}`}
      data-average-fps={runtime.averageFps ?? "NOT_MEASURED"}
      data-p95-frame-time={runtime.p95FrameTimeMs ?? "NOT_MEASURED"}
      data-texture-memory-mb={runtime.estimatedTextureMemoryMb}
      data-webgl-errors={runtime.webglErrors}
    >
      <div className="globe-canvas" aria-label={labels.instructions}>
        {webglState === "CHECKING" ? (
          <div className="globe-initialising" aria-live="polite">
            {labels.instructions}
          </div>
        ) : null}
        {showPoster ? <div className="globe-poster">{labels.fallback}</div> : null}
        {webglState === "SUPPORTED" || webglState === "READY" ? (
          <GlobeErrorBoundary onFailure={failWebGl}>
            <Canvas
              camera={{ position: [0, 0, 4.65], fov: 38, near: 0.1, far: 100 }}
              dpr={[1, 2]}
              gl={{
                antialias: true,
                alpha: true,
                powerPreference: "high-performance"
              }}
              fallback={<span className="globe-canvas-fallback-text">{labels.fallback}</span>}
              onCreated={({ gl }) => {
                gl.outputColorSpace = THREE.SRGBColorSpace;
                gl.toneMapping = THREE.ACESFilmicToneMapping;
                gl.toneMappingExposure = 1;
                setWebglState("READY");
                updateRuntime({ contextState: "READY" });
              }}
            >
              <Suspense fallback={null}>
                <GlobeScene
                  progressRef={progressRef}
                  reducedMotion={reducedMotion}
                  lightTheme={lightTheme}
                  onSelect={selectSource}
                  onRuntime={updateRuntime}
                  onContextFailure={failWebGl}
                />
              </Suspense>
            </Canvas>
          </GlobeErrorBoundary>
        ) : null}
      </div>

      <div className="globe-interface">
        <div className="globe-selected" data-state={selected.state} aria-live="polite">
          <span>{selected.jurisdiction}</span>
          <strong>{selected.name}</strong>
          <small>
            {labels.legend[selected.state]} · {selected.access.replaceAll("_", " ")}
          </small>
        </div>
        <details className="source-table">
          <summary>{labels.tableCaption}</summary>
          <div tabIndex={0}>
            <table>
              <caption>{labels.tableCaption}</caption>
              <thead>
                <tr>
                  <th scope="col">{labels.source}</th>
                  <th scope="col">{labels.jurisdiction}</th>
                  <th scope="col">{labels.state}</th>
                </tr>
              </thead>
              <tbody>
                {sourcePoints.map((source) => (
                  <tr key={source.id}>
                    <th scope="row">{source.name}</th>
                    <td>{source.jurisdiction}</td>
                    <td>
                      {labels.legend[source.state]} · {source.access.replaceAll("_", " ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </div>
    </div>
  );
}
