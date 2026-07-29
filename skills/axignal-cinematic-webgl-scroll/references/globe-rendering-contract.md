# Globe Rendering Contract

## Objective

Render the AXIGNAL Globe as a scientific product instrument with stable depth, readable geography, semantic overlays and deterministic lifecycle behavior.

## Scene architecture

Use one mounted `Canvas` and one scene root for the cinematic sequence. Camera state, Globe state and overlay state may change, but the semantic Globe must not be replaced by unrelated artwork.

Recommended scene graph:

```text
Canvas
└── CinematicGlobeScene
    ├── CameraRig
    ├── EarthGroup
    │   ├── EarthSurface
    │   ├── NightLights
    │   ├── Clouds
    │   ├── Atmosphere
    │   ├── Boundaries
    │   ├── TerritoryMarkers
    │   └── ActivityArcs
    ├── EvidenceTransitionLayer
    └── GraphTransitionLayer
```

## Renderer configuration

Record and justify:

- `gl.outputColorSpace`;
- tone mapping and exposure;
- antialias setting;
- alpha and premultiplied-alpha behavior;
- power preference;
- effective DPR;
- maximum texture size;
- maximum anisotropy;
- WebGL version.

Color textures use `SRGBColorSpace`. Data textures such as normal, roughness, displacement, masks and scalar maps remain in a non-color space.

## Earth surface

The Earth surface must remain legible through day and night transitions. Avoid crushed blacks, clipped highlights and cloud opacity that hides the land.

Required properties:

- physically coherent directional lighting or a documented custom shader;
- stable normal orientation;
- correct UV seam handling;
- mipmaps for minification;
- bounded anisotropy;
- no UI or borders baked into albedo;
- no dynamic allocation in `useFrame`.

## Atmosphere

Implement atmosphere and rim lighting procedurally. The effect must derive from view direction and surface normal rather than a flat sprite.

The atmosphere must:

- preserve the silhouette;
- avoid a uniform neon ring;
- remain subtle behind labels;
- reduce on constrained devices;
- dispose materials on unmount.

## Clouds

Clouds use a separate shell or shader layer. They must:

- rotate independently and slowly;
- use a lower opacity than the land contrast;
- have a measured texture tier;
- not become the dominant source of blur;
- support disabling under performance pressure;
- avoid z-fighting with the surface.

## Geographic overlays

Country borders, markers and arcs are vector or procedural geometry. Their meaning must be explicit and accessible.

Use instancing or batched geometry for repeated markers. Cap arc density by device tier and narrative scene. Avoid transparent overdraw across the entire Globe.

## Camera

Camera movement must be deterministic and controlled by a typed scene state or the master ScrollTrigger timeline. User orbit controls are disabled during pinned choreography unless the task explicitly requires reversible direct manipulation.

Near and far planes must avoid depth precision artifacts. Camera motion must not pass through the Globe or expose texture seams.

## Lifecycle

On unmount or route transition:

- kill ScrollTriggers owned by the scene;
- remove listeners;
- cancel pending asset loads where possible;
- dispose generated geometries, materials and textures;
- avoid duplicate Canvas instances;
- stop animation when the scene is not visible.

## Failure states

Fail the gate when:

- Canvas drawing buffer is materially below the intended tier;
- the poster remains visible over initialized WebGL;
- the Earth is a flat image disguised as a Globe;
- regions become visibly pixelated before the configured semantic zoom threshold;
- atmosphere or clouds obscure geography;
- WebGL errors occur;
- multiple scene roots compete for the same narrative state.
