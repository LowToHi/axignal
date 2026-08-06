# AXIGNAL cinematic WebGL rendering contract

Goal ID: `AXIGNAL-GOAL-001`

## Composition contract

```text
axignal-gsap-ui-ux
→ owns scroll choreography and semantic motion

axignal-cinematic-webgl-scroll
→ owns the render quality of the Globe controlled by that choreography
```

Maintain:

```text
one Canvas
→ one Globe scene
→ one camera system
→ one scroll progress source
```

## Texture tiers

| Tier | Selection baseline | Global albedo | Europe LOD | Maximum DPR |
|---|---|---:|---:|---:|
| `mobile` | narrow viewport, WebGL1, ≤4 GB reported memory or constrained texture limit | ≥2048×1024 | ≥1024 px wide | 1.35 |
| `desktop-standard` | WebGL2 and `MAX_TEXTURE_SIZE ≥ 4096` | ≥4096×2048 | ≥2048 px wide | 1.65 |
| `desktop-high` | WebGL2, viewport ≥1280, device DPR ≥1.5, memory ≥8 GB and `MAX_TEXTURE_SIZE ≥ 8192` | native high-quality source or GPU-compressed 8K | ≥3072 px wide | 2 |

Do not upscale a source and claim new geographic information. A regional derivative may improve local sampling, compression and tonal detail, but the report must preserve the source resolution.

Use KTX2/Basis when a pinned reproducible encoder exists. Otherwise use measured high-quality WebP/JPEG and record:

```text
BLOCKED_NO_PINNED_ENCODER
```

KTX2 absence alone is not a failure.

## Texture contract

For every texture record:

- source path and derivative path;
- dimensions, format, bytes and alpha;
- color-space intent;
- mipmap, min/mag filter, anisotropy and wrap policy;
- tier and role;
- source page, rights basis, transformation and checksum.

Color maps use `SRGBColorSpace`, trilinear minification, linear magnification and bounded device anisotropy. Data maps must declare their non-color color space.

## Europe LOD contract

The regional state machine is:

```text
NOT_REQUESTED
→ REQUESTED before SCENE_EUROPE crossfade
→ LOADED
→ ACTIVE through shader blend
→ INACTIVE when leaving the close view
```

The runtime must expose:

- requested;
- loaded;
- active;
- load duration;
- failed;
- fallback used.

Use a feathered shader mask. Reject visible seams, flashes, exposure changes or main-thread blocking. LOD failure must retain the global texture and narrative.

## Canvas and adaptive DPR

Measure:

- CSS width/height;
- drawing-buffer width/height;
- device DPR;
- effective DPR per axis;
- WebGL version;
- GPU renderer when exposed;
- maximum texture size and anisotropy;
- output and unpack color spaces.

Use multi-second sample windows. Require at least two degraded windows before reducing DPR and at least three healthy windows before bounded recovery. Change DPR in steps no smaller than 0.125 and no more frequently than once per measurement window.

## Rendering performance

- Pause the frame loop when the Globe is offscreen or the document is hidden.
- Reuse geometries and materials.
- Instance repeated markers.
- Merge static arc geometry when semantics and material state match.
- Avoid per-frame object construction.
- Dispose owned textures, geometries, shaders, observers and listeners.
- Degrade cloud opacity or disable clouds before removing semantic layers.

Initial acceptance targets:

```text
desktop average FPS >= 55
desktop p95 frame time <= 24 ms
desktop no sustained period below 45 FPS
capable desktop effective DPR >= 1.5

mobile average FPS >= 30
mobile no sustained period below 24 FPS
no decode freeze > 200 ms
```

Software-rendered headless results are diagnostic only. Use `NOT_MEASURED_PHYSICAL_GPU` for device claims not measured on physical hardware.

## Texture memory

Estimate uncompressed GPU memory per tier:

```text
width × height × bytes-per-pixel × mip factor
```

Use four bytes per texel and a `4/3` mip factor for RGBA8/sRGB estimates unless the actual compressed format is known. Report initial and deferred texture memory separately.

## Vector boundaries

Load licensed GeoJSON as an independent line layer. Adapt coordinate stride/density by tier. Do not rely solely on boundaries baked into the albedo. Avoid connecting coordinates across the antimeridian.

## Fallback lifecycle

The poster may load only when:

- WebGL is unsupported;
- Canvas initialization fails;
- context loss cannot recover;
- an explicit performance policy declines WebGL.

The healthy WebGL resource list must not contain the poster. Canvas fallback markup must not reference its URL.

## Sharpness evidence

Compare before and after with identical:

- browser and viewport;
- device DPR and effective DPR;
- drawing-buffer size;
- scroll progress;
- camera position and Earth rotation;
- tier and LOD state.

The human gate evaluates coastlines, independent borders, Europe, cloud veil, halo, arcs, labels, zoom continuity and seams.
