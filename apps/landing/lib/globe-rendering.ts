import * as THREE from "three";

export type GlobeTextureTier = "mobile" | "desktop-standard" | "desktop-high";

export type GlobeTierConfig = {
  id: GlobeTextureTier;
  globalAsset: string;
  globalSize: readonly [number, number];
  regionalAsset: string;
  regionalSize: readonly [number, number];
  cloudAsset: string;
  cloudSize: readonly [number, number];
  maxDpr: number;
  boundaryStride: number;
  albedoAnisotropy: number;
  cloudAnisotropy: number;
};

export type GlobeCapabilityInput = {
  viewportWidth: number;
  devicePixelRatio: number;
  deviceMemory: number;
  maxTextureSize: number;
  webgl2: boolean;
  reducedMotion: boolean;
};

export type GlobeRuntimeTelemetry = {
  textureTier: GlobeTextureTier | "pending";
  lodRequested: boolean;
  lodLoaded: boolean;
  lodActive: boolean;
  lodLoadMs: number | null;
  lodFailure: string | null;
  lodFallback: "NONE" | "GLOBAL_TEXTURE";
  boundaryLayer: "PENDING" | "ACTIVE" | "FAILED";
  boundaryLodRequested: boolean;
  boundaryLodLoaded: boolean;
  boundaryLodActive: boolean;
  boundaryLodFailure: string | null;
  effectiveDpr: number;
  drawingBufferWidth: number;
  drawingBufferHeight: number;
  averageFps: number | null;
  p95FrameTimeMs: number | null;
  estimatedTextureMemoryMb: number;
  webglErrors: number;
  renderer: string;
  maxTextureSize: number;
  maxAnisotropy: number;
  contextState: "CHECKING" | "READY" | "FAILED" | "UNSUPPORTED";
};

export const GLOBE_TIER_CONFIGS: Record<GlobeTextureTier, GlobeTierConfig> = {
  mobile: {
    id: "mobile",
    globalAsset: "/globe/earth-albedo-mobile.webp",
    globalSize: [2048, 1024],
    regionalAsset: "/globe/earth-europe-mobile.webp",
    regionalSize: [1024, 635],
    cloudAsset: "/globe/earth-clouds-mobile.webp",
    cloudSize: [1024, 512],
    maxDpr: 1.35,
    boundaryStride: 2,
    albedoAnisotropy: 4,
    cloudAnisotropy: 2
  },
  "desktop-standard": {
    id: "desktop-standard",
    globalAsset: "/globe/earth-albedo.webp",
    globalSize: [4096, 2048],
    regionalAsset: "/globe/earth-europe.webp",
    regionalSize: [2048, 1269],
    cloudAsset: "/globe/earth-clouds.webp",
    cloudSize: [2048, 1024],
    maxDpr: 1.65,
    boundaryStride: 1,
    albedoAnisotropy: 8,
    cloudAnisotropy: 4
  },
  "desktop-high": {
    id: "desktop-high",
    globalAsset: "/globe/earth-albedo-high.webp",
    globalSize: [5400, 2700],
    regionalAsset: "/globe/earth-europe-high.webp",
    regionalSize: [3072, 1904],
    cloudAsset: "/globe/earth-clouds.webp",
    cloudSize: [2048, 1024],
    maxDpr: 2,
    boundaryStride: 1,
    albedoAnisotropy: 16,
    cloudAnisotropy: 8
  }
};

export const EUROPE_LOD_BOUNDS = new THREE.Vector4(
  (-26 + 180) / 360,
  (28 + 90) / 180,
  (45 + 180) / 360,
  (72 + 90) / 180
);

export function selectGlobeTextureTier(input: GlobeCapabilityInput): GlobeTextureTier {
  const constrained =
    input.viewportWidth < 768 ||
    input.deviceMemory <= 4 ||
    input.maxTextureSize < 4096 ||
    !input.webgl2;
  if (constrained) return "mobile";

  const highCapacity =
    input.viewportWidth >= 1280 &&
    input.devicePixelRatio >= 1.5 &&
    input.deviceMemory >= 8 &&
    input.maxTextureSize >= 8192 &&
    input.webgl2 &&
    !input.reducedMotion;

  return highCapacity ? "desktop-high" : "desktop-standard";
}

function textureBytes([width, height]: readonly [number, number]) {
  return width * height * 4 * (4 / 3);
}

export function estimateTextureMemoryMb(
  config: GlobeTierConfig,
  options: { regionalLoaded: boolean; cloudsEnabled: boolean }
) {
  const bytes =
    textureBytes(config.globalSize) +
    (options.regionalLoaded ? textureBytes(config.regionalSize) : 0) +
    (options.cloudsEnabled ? textureBytes(config.cloudSize) : 0);
  return Number((bytes / 1024 / 1024).toFixed(1));
}

export function latLonToVector(latitude: number, longitude: number, radius = 1.51) {
  const phi = (90 - latitude) * (Math.PI / 180);
  const theta = (longitude + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -(radius * Math.sin(phi) * Math.cos(theta)),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

type GeoJsonGeometry = {
  type?: "Polygon" | "MultiPolygon" | "LineString" | "MultiLineString";
  coordinates?: unknown;
};

type GeoJsonDocument = {
  features?: Array<{ geometry?: GeoJsonGeometry }>;
};

function geometryRings(geometry: GeoJsonGeometry | undefined): number[][][] {
  if (!geometry?.coordinates) return [];
  if (geometry.type === "Polygon") return geometry.coordinates as number[][][];
  if (geometry.type === "MultiPolygon") {
    return (geometry.coordinates as number[][][][]).flatMap((polygon) => polygon);
  }
  if (geometry.type === "LineString") return [geometry.coordinates as number[][]];
  if (geometry.type === "MultiLineString") return geometry.coordinates as number[][][];
  return [];
}

export function createBoundaryGeometry(document: GeoJsonDocument, stride: number) {
  const positions: number[] = [];
  const appendSegment = (from: number[], to: number[]) => {
    const fromLongitude = Number(from[0]);
    const toLongitude = Number(to[0]);
    if (!Number.isFinite(fromLongitude) || !Number.isFinite(toLongitude)) return;
    if (Math.abs(fromLongitude - toLongitude) > 180) return;

    const start = latLonToVector(Number(from[1]), fromLongitude, 1.488);
    const end = latLonToVector(Number(to[1]), toLongitude, 1.488);
    positions.push(start.x, start.y, start.z, end.x, end.y, end.z);
  };

  for (const feature of document.features ?? []) {
    for (const ring of geometryRings(feature.geometry)) {
      if (ring.length < 2) continue;
      let previous = ring[0]!;
      for (let index = stride; index < ring.length; index += stride) {
        const current = ring[index]!;
        appendSegment(previous, current);
        previous = current;
      }
      const finalPoint = ring[ring.length - 1]!;
      if (previous !== finalPoint) appendSegment(previous, finalPoint);
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.computeBoundingSphere();
  return geometry;
}
