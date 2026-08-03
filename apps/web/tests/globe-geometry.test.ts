import assert from "node:assert/strict";
import test from "node:test";
import * as THREE from "three";

import {
  createBoundaryGeometry,
  latLonToVector,
  northUpFocusRotation,
} from "../components/subscriber/intelligence/globe-geometry";

test("lat/lon markers project to the intended cardinal points", () => {
  const equator = latLonToVector(0, 0, 2);
  const northPole = latLonToVector(90, 0, 2);

  assert.ok(Math.abs(equator.length() - 2) < 0.000001);
  assert.ok(Math.abs(northPole.x) < 0.000001);
  assert.equal(northPole.y, 2);
  assert.ok(Math.abs(northPole.z) < 0.000001);
});

test("focus rotation keeps geographic north vertical", () => {
  const focus = latLonToVector(40, -3, 1).normalize();
  const north = new THREE.Vector3(0, 1, 0);
  const northTangent = north
    .clone()
    .addScaledVector(focus, -north.dot(focus))
    .normalize();
  const rotation = northUpFocusRotation(focus, new THREE.Euler());

  const focusedPoint = focus.clone().applyEuler(rotation);
  const focusedNorth = northTangent.clone().applyEuler(rotation);

  assert.ok(focusedPoint.distanceTo(new THREE.Vector3(0, 0, 1)) < 0.000001);
  assert.ok(focusedNorth.distanceTo(new THREE.Vector3(0, 1, 0)) < 0.000001);
});

test("boundary geometry retains local country edges and rejects dateline chords", () => {
  const geometry = createBoundaryGeometry({
    features: [
      {
        geometry: {
          type: "LineString",
          coordinates: [
            [0, 0],
            [1, 0],
            [179, 0],
            [-179, 0],
          ],
        },
      },
    ],
  });

  const positions = geometry.getAttribute("position");
  assert.equal(
    positions.count,
    4,
    "only the two non-dateline segments are rendered",
  );
  geometry.dispose();
});
