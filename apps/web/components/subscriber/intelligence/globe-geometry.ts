import * as THREE from "three";

export type GeoJsonGeometry = {
  type?: "Polygon" | "MultiPolygon" | "LineString" | "MultiLineString";
  coordinates?: unknown;
};

export type GeoJsonDocument = {
  features?: Array<{ geometry?: GeoJsonGeometry }>;
};

export function latLonToVector(
  latitude: number,
  longitude: number,
  radius = 1.51,
) {
  const phi = (90 - latitude) * (Math.PI / 180);
  const theta = (longitude + 180) * (Math.PI / 180);

  return new THREE.Vector3(
    -(radius * Math.sin(phi) * Math.cos(theta)),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  );
}

/**
 * Builds a globe rotation that puts a focus point in front of the camera while
 * keeping geographic north at the top of the viewport. The explicit local
 * tangent basis avoids the arbitrary roll introduced by a shortest-arc
 * quaternion when the focus point changes.
 */
export function northUpFocusRotation(
  focusPoint: THREE.Vector3,
  fallback: THREE.Euler,
) {
  const forward = focusPoint.clone().normalize();
  if (forward.lengthSq() < 0.0001) return fallback.clone();

  const geographicNorth = new THREE.Vector3(0, 1, 0);
  const up = geographicNorth
    .clone()
    .addScaledVector(forward, -geographicNorth.dot(forward));
  if (up.lengthSq() < 0.0001) return fallback.clone();
  up.normalize();

  const right = new THREE.Vector3().crossVectors(up, forward).normalize();
  const sourceBasis = new THREE.Matrix4().makeBasis(right, up, forward);
  const rotation = new THREE.Quaternion()
    .setFromRotationMatrix(sourceBasis)
    .invert();

  return new THREE.Euler().setFromQuaternion(rotation);
}

function geometryRings(geometry: GeoJsonGeometry | undefined): number[][][] {
  if (!geometry?.coordinates) return [];

  if (geometry.type === "Polygon") return geometry.coordinates as number[][][];
  if (geometry.type === "MultiPolygon") {
    return (geometry.coordinates as number[][][][]).flatMap(
      (polygon) => polygon,
    );
  }
  if (geometry.type === "LineString")
    return [geometry.coordinates as number[][]];
  if (geometry.type === "MultiLineString")
    return geometry.coordinates as number[][][];

  return [];
}

/**
 * Projects Natural Earth GeoJSON rings onto the same sphere used by the Earth map.
 * Dateline-spanning segments are deliberately omitted; a straight line across the
 * globe would be a cartographic error rather than a useful boundary.
 */
export function createBoundaryGeometry(
  document: GeoJsonDocument,
  stride = 1,
  radius = 1.493,
) {
  const positions: number[] = [];
  const safeStride = Math.max(1, Math.floor(stride));

  const appendSegment = (from: number[], to: number[]) => {
    const fromLongitude = Number(from[0]);
    const toLongitude = Number(to[0]);
    const fromLatitude = Number(from[1]);
    const toLatitude = Number(to[1]);

    if (
      ![fromLongitude, toLongitude, fromLatitude, toLatitude].every(
        Number.isFinite,
      )
    )
      return;
    if (Math.abs(fromLongitude - toLongitude) > 180) return;

    const start = latLonToVector(fromLatitude, fromLongitude, radius);
    const end = latLonToVector(toLatitude, toLongitude, radius);
    positions.push(start.x, start.y, start.z, end.x, end.y, end.z);
  };

  for (const feature of document.features ?? []) {
    for (const ring of geometryRings(feature.geometry)) {
      if (ring.length < 2) continue;
      let previous = ring[0]!;
      for (let index = safeStride; index < ring.length; index += safeStride) {
        const current = ring[index]!;
        appendSegment(previous, current);
        previous = current;
      }

      const finalPoint = ring[ring.length - 1]!;
      if (previous !== finalPoint) appendSegment(previous, finalPoint);
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(positions, 3),
  );
  geometry.computeBoundingSphere();
  return geometry;
}
