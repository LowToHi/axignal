# Texture Quality Contract

## Purpose

Prevent low-resolution, wasteful or unlicensed Globe assets from reaching visual review.

## Texture manifest

Every texture must declare:

```text
asset_id
path
role
source_url or source organisation
licence
attribution
transformations
format
width
height
file_bytes
color_space
alpha
mipmaps
min_filter
mag_filter
anisotropy_policy
device_tier
load_phase
```

Unknown provenance or licence results in `BLOCKED`.

## Recommended tiers

These are starting targets, not permission to load every asset simultaneously.

### Mobile

- global albedo: up to 4096 × 2048;
- clouds: 2048–4096 wide;
- night lights: 2048–4096 wide;
- effective DPR: approximately 1–1.5;
- reduced marker and arc density.

### Desktop

- global albedo: up to 8192 × 4096 when supported;
- clouds: approximately 4096 wide;
- night lights: 4096–8192 wide;
- effective DPR: up to 2 on capable hardware;
- anisotropy bounded by renderer capability.

### Regional Europe

When Europe occupies a large fraction of the viewport, use one of:

1. regional high-density overlay blended by a geographic mask;
2. tiled texture system;
3. clipmap or equivalent multi-resolution strategy.

Do not stretch a single global texture indefinitely.

## Formats

Priority:

1. KTX2/Basis GPU-compressed textures when the deployment pipeline supports them;
2. WebP or JPEG for opaque source imagery;
3. PNG only where lossless alpha or exact data preservation is required.

Do not use a large uncompressed PNG for global albedo without measured evidence.

## Memory estimation

Report both transfer bytes and approximate decoded GPU memory. A rough uncompressed RGBA estimate is:

```text
width × height × 4 × mip_factor
```

Use a mip factor near `1.333` for a complete mip chain. GPU compression changes the estimate and must be reported according to the selected format.

## Filtering

For color textures:

- enable mipmaps unless the format or use case prohibits them;
- use a mipmap minification filter;
- use linear magnification;
- set anisotropy after the renderer is available;
- never exceed `renderer.capabilities.getMaxAnisotropy()`.

## LOD transition

Regional LOD must:

- preload before it is visible;
- crossfade or blend without flashing;
- preserve color and exposure continuity;
- avoid a visible hard geographic seam;
- fall back safely if loading fails;
- release memory when no longer needed if the scene budget requires it.

Record the threshold and active LOD in telemetry and scene captures.

## Poster

The poster is a lightweight fallback or loading representation. It must not remain over the initialized Canvas. Its dimensions and compression must be separately declared; poster quality does not count as Globe render quality.

## Rejection conditions

Fail when:

- a required texture has unknown dimensions or provenance;
- desktop close-up uses an insufficient global texture without LOD;
- mobile loads the complete desktop texture set without justification;
- texture color spaces are wrong;
- mipmaps or anisotropy are absent without evidence;
- the cloud layer visibly destroys surface detail;
- duplicate downloads occur for the same content hash;
- regional LOD blocks first hero render;
- a large raster contains baked borders, labels, markers or interface elements.
