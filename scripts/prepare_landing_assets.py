#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
LANDING_PUBLIC = ROOT / "apps" / "landing" / "public"
WEB_BRAND = ROOT / "apps" / "web" / "public" / "brand"
PROVENANCE = ROOT / "docs" / "landing" / "asset-provenance.generated.json"
EUROPE_BOUNDS = (-26.0, 28.0, 45.0, 72.0)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def project(longitude: float, latitude: float, width: int, height: int) -> tuple[float, float]:
    return ((longitude + 180) / 360 * width, (90 - latitude) / 180 * height)


def geometry_lines(geometry: dict) -> list[list[list[float]]]:
    coordinates = geometry.get("coordinates", [])
    if geometry.get("type") == "Polygon":
        return coordinates
    if geometry.get("type") == "MultiPolygon":
        return [ring for polygon in coordinates for ring in polygon]
    if geometry.get("type") == "LineString":
        return [coordinates]
    if geometry.get("type") == "MultiLineString":
        return coordinates
    return []


def shapefile_lines(zip_path: Path) -> list[list[tuple[float, float]]]:
    with ZipFile(zip_path) as archive:
        shp_name = next(
            (name for name in archive.namelist() if name.lower().endswith(".shp")),
            None,
        )
        if shp_name is None:
            raise ValueError(f"No .shp file found in {zip_path}")
        data = archive.read(shp_name)

    lines: list[list[tuple[float, float]]] = []
    offset = 100
    while offset + 8 <= len(data):
        _, content_words = struct.unpack_from(">2i", data, offset)
        offset += 8
        content_bytes = content_words * 2
        record_end = offset + content_bytes
        if record_end > len(data) or content_bytes < 4:
            raise ValueError(f"Invalid shapefile record in {zip_path}")

        shape_type = struct.unpack_from("<i", data, offset)[0]
        if shape_type in (3, 5, 13, 15):
            part_count, point_count = struct.unpack_from("<2i", data, offset + 36)
            parts_offset = offset + 44
            points_offset = parts_offset + part_count * 4
            part_indexes = list(
                struct.unpack_from(f"<{part_count}i", data, parts_offset)
            )
            points = [
                struct.unpack_from("<2d", data, points_offset + index * 16)
                for index in range(point_count)
            ]
            for part_index, start in enumerate(part_indexes):
                end = (
                    part_indexes[part_index + 1]
                    if part_index + 1 < len(part_indexes)
                    else point_count
                )
                if end - start >= 2:
                    lines.append(points[start:end])
        offset = record_end
    return lines


def clip_segment(
    start: tuple[float, float],
    end: tuple[float, float],
    bounds: tuple[float, float, float, float],
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    west, south, east, north = bounds
    x0, y0 = start
    x1, y1 = end
    dx = x1 - x0
    dy = y1 - y0
    lower = 0.0
    upper = 1.0

    for direction, distance in (
        (-dx, x0 - west),
        (dx, east - x0),
        (-dy, y0 - south),
        (dy, north - y0),
    ):
        if direction == 0:
            if distance < 0:
                return None
            continue
        ratio = distance / direction
        if direction < 0:
            lower = max(lower, ratio)
        else:
            upper = min(upper, ratio)
        if lower > upper:
            return None

    return (
        (x0 + lower * dx, y0 + lower * dy),
        (x0 + upper * dx, y0 + upper * dy),
    )


def clipped_lines(
    lines: list[list[tuple[float, float]]],
    bounds: tuple[float, float, float, float],
) -> list[list[list[float]]]:
    clipped: list[list[list[float]]] = []
    for line in lines:
        current: list[list[float]] = []
        for index in range(1, len(line)):
            segment = clip_segment(line[index - 1], line[index], bounds)
            if segment is None:
                if len(current) >= 2:
                    clipped.append(current)
                current = []
                continue

            start, end = segment
            rounded_start = [round(start[0], 5), round(start[1], 5)]
            rounded_end = [round(end[0], 5), round(end[1], 5)]
            if current and current[-1] == rounded_start:
                if current[-1] != rounded_end:
                    current.append(rounded_end)
            else:
                if len(current) >= 2:
                    clipped.append(current)
                current = (
                    [rounded_start, rounded_end]
                    if rounded_start != rounded_end
                    else []
                )
        if len(current) >= 2:
            clipped.append(current)
    return clipped


def save_europe_boundaries(
    boundary_zip: Path,
    coastline_zip: Path,
    destination: Path,
) -> None:
    features = []
    for layer, source in (
        ("ADMIN_0_BOUNDARY", boundary_zip),
        ("COASTLINE", coastline_zip),
    ):
        coordinates = clipped_lines(shapefile_lines(source), EUROPE_BOUNDS)
        features.append(
            {
                "type": "Feature",
                "properties": {"layer": layer, "scale": "1:50m"},
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": coordinates,
                },
            }
        )

    destination.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "axignal_europe_boundaries_50m",
                "bbox": list(EUROPE_BOUNDS),
                "features": features,
            },
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def overlay_boundaries(image: Image.Image, geojson_path: Path) -> Image.Image:
    document = json.loads(geojson_path.read_text(encoding="utf-8"))
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for feature in document.get("features", []):
        for ring in geometry_lines(feature.get("geometry", {})):
            points = [project(float(lon), float(lat), image.width, image.height) for lon, lat, *_ in ring]
            if len(points) > 1:
                draw.line(points, fill=(155, 220, 215, 82), width=max(1, image.width // 1600))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def save_webp(image: Image.Image, destination: Path, width: int, quality: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    ratio = width / image.width
    resized = image.resize((width, round(image.height * ratio)), Image.Resampling.LANCZOS)
    resized.save(destination, "WEBP", quality=quality, method=6)


def regional_crop(
    image: Image.Image,
    *,
    west: float = -26,
    north: float = 72,
    east: float = 45,
    south: float = 28,
) -> Image.Image:
    left, top = project(west, north, image.width, image.height)
    right, bottom = project(east, south, image.width, image.height)
    return image.crop((round(left), round(top), round(right), round(bottom)))


def save_regional_webp(
    image: Image.Image,
    destination: Path,
    width: int,
    quality: int,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    ratio = width / image.width
    resized = image.resize((width, round(image.height * ratio)), Image.Resampling.LANCZOS)
    sharpened = resized.filter(ImageFilter.UnsharpMask(radius=0.8, percent=52, threshold=3))
    sharpened.save(destination, "WEBP", quality=quality, method=6)


def save_cloud_webp(
    image: Image.Image,
    destination: Path,
    width: int,
    quality: int,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    ratio = width / image.width
    resized = image.resize((width, round(image.height * ratio)), Image.Resampling.LANCZOS)
    luminance = ImageOps.autocontrast(resized.convert("L"), cutoff=(1, 1))
    alpha = luminance.point(
        lambda value: 0
        if value < 10
        else min(255, round((((value - 10) / 245) ** 0.82) * 255))
    )
    clouds = Image.new("RGBA", resized.size, (235, 247, 249, 0))
    clouds.putalpha(alpha)
    clouds.save(destination, "WEBP", quality=quality, method=4)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def social_image(image: Image.Image, destination: Path) -> None:
    canvas = image.resize((1200, 630), Image.Resampling.LANCZOS).convert("RGBA")
    canvas = Image.alpha_composite(canvas, Image.new("RGBA", canvas.size, (2, 10, 14, 180)))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((70, 64, 76, 566), fill=(0, 225, 207, 255))
    draw.text((112, 80), "AXIGNAL", fill=(231, 242, 241), font=font(42, bold=True))
    draw.text(
        (112, 210),
        "PUBLIC PROCUREMENT\nINTELLIGENCE",
        fill=(231, 242, 241),
        font=font(62, bold=True),
        spacing=4,
    )
    draw.text(
        (112, 402),
        "Evidence-governed intelligence for organisations\nthat sell to government.",
        fill=(176, 199, 199),
        font=font(25),
        spacing=7,
    )
    draw.text(
        (112, 530),
        "SYNTHETIC PRODUCT DEMONSTRATION",
        fill=(0, 225, 207),
        font=font(15, bold=True),
    )
    canvas.convert("RGB").save(destination, "JPEG", quality=88, optimize=True, progressive=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare reproducible AXIGNAL landing assets")
    parser.add_argument("--source-dir", type=Path, required=True)
    args = parser.parse_args()

    source_image = args.source_dir / "world.200402.3x5400x2700.jpg"
    source_clouds = args.source_dir / "cloud_combined_2048.jpg"
    geojson = args.source_dir / "ne_110m_admin_0_countries.geojson"
    boundaries_50m = args.source_dir / "ne_50m_admin_0_boundary_lines_land.zip"
    coastline_50m = args.source_dir / "ne_50m_coastline.zip"
    required_sources = (
        source_image,
        source_clouds,
        geojson,
        boundaries_50m,
        coastline_50m,
    )
    if not all(path.is_file() for path in required_sources):
        raise SystemExit(
            "NASA Earth/cloud images and Natural Earth 110m/50m sources are required"
        )

    brand_dir = LANDING_PUBLIC / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    brand_assets = ["axignal-logo.svg", "axignal-logo-dark.svg", "axignal-isotipo.svg"]
    for name in brand_assets:
        shutil.copyfile(WEB_BRAND / name, brand_dir / name)

    image = Image.open(source_image).convert("RGB")
    image = ImageEnhance.Contrast(image).enhance(1.06)
    image = ImageEnhance.Color(image).enhance(0.84)
    image = image.filter(ImageFilter.UnsharpMask(radius=0.55, percent=26, threshold=3))

    globe_dir = LANDING_PUBLIC / "globe"
    save_webp(image, globe_dir / "earth-albedo-mobile.webp", 2048, 84)
    save_webp(image, globe_dir / "earth-albedo.webp", 4096, 92)
    save_webp(image, globe_dir / "earth-albedo-high.webp", 5400, 95)

    europe = regional_crop(image)
    save_regional_webp(europe, globe_dir / "earth-europe-mobile.webp", 1024, 88)
    save_regional_webp(europe, globe_dir / "earth-europe.webp", 2048, 93)
    save_regional_webp(europe, globe_dir / "earth-europe-high.webp", 3072, 95)

    with Image.open(source_clouds) as cloud_image:
        save_cloud_webp(cloud_image, globe_dir / "earth-clouds-mobile.webp", 1024, 84)
        save_cloud_webp(cloud_image, globe_dir / "earth-clouds.webp", 2048, 91)

    poster_source = overlay_boundaries(image, geojson)
    poster = poster_source.crop((1180, 260, 4320, 2700))
    poster = ImageEnhance.Brightness(poster).enhance(0.56)
    save_webp(poster, globe_dir / "globe-poster.webp", 1280, 78)
    save_webp(poster, LANDING_PUBLIC / "seo-hero.webp", 1600, 80)
    social_image(poster, LANDING_PUBLIC / "opengraph-image.jpg")
    shutil.copyfile(LANDING_PUBLIC / "opengraph-image.jpg", LANDING_PUBLIC / "twitter-image.jpg")

    geo_destination = globe_dir / "countries-110m.simplified.geojson"
    shutil.copyfile(geojson, geo_destination)
    save_europe_boundaries(
        boundaries_50m,
        coastline_50m,
        globe_dir / "europe-boundaries-50m.geojson",
    )

    assets = []
    for path in sorted(LANDING_PUBLIC.rglob("*")):
        if path.is_file():
            assets.append(
                {
                    "file": path.relative_to(ROOT).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": digest(path),
                }
            )

    record = {
        "version": "1.1.0",
        "status": "LOCAL_DERIVATIVES_PREPARED",
        "sources": [
            {
                "id": "earth-albedo-february",
                "file": str(source_image),
                "sha256": digest(source_image),
                "source_page": "https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/base-map/",
                "rights": "NASA imagery used factually without endorsement; NASA credited.",
            },
            {
                "id": "earth-clouds-2002",
                "file": str(source_clouds),
                "sha256": digest(source_clouds),
                "source_page": "https://visibleearth.nasa.gov/images/57747/blue-marble-clouds/77558l",
                "rights": "NASA imagery used factually without endorsement; NASA credited.",
            },
            {
                "id": "countries-110m",
                "file": str(geojson),
                "sha256": digest(geojson),
                "source_page": "https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/",
                "rights": "Natural Earth public domain.",
            },
            {
                "id": "boundaries-50m",
                "file": str(boundaries_50m),
                "sha256": digest(boundaries_50m),
                "source_page": "https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-boundary-lines-2/",
                "rights": "Natural Earth public domain; version 5.1.0; de facto boundary policy.",
            },
            {
                "id": "coastline-50m",
                "file": str(coastline_50m),
                "sha256": digest(coastline_50m),
                "source_page": "https://www.naturalearthdata.com/downloads/50m-physical-vectors/50m-coastline/",
                "rights": "Natural Earth public domain; version 5.1.0.",
            },
        ],
        "assets": assets,
        "generation": {
            "script": "scripts/prepare_landing_assets.py",
            "texture_tiers": {
                "mobile": "2048px WebP",
                "desktop-standard": "4096px high-quality WebP",
                "desktop-high": "5400px native-resolution high-quality WebP",
            },
            "regional_lod": {
                "bounds": {"west": -26, "north": 72, "east": 45, "south": 28},
                "mobile": "1024px WebP",
                "desktop-standard": "2048px WebP",
                "desktop-high": "3072px WebP",
                "transition": "runtime shader crossfade",
            },
            "boundaries": {
                "global": "Natural Earth 110m countries retained as the initial independent runtime layer",
                "europe_lod": "Natural Earth 50m land boundaries and coastline clipped to Europe and lazy-loaded on capable desktop tiers",
                "bounds": {
                    "west": EUROPE_BOUNDS[0],
                    "south": EUROPE_BOUNDS[1],
                    "east": EUROPE_BOUNDS[2],
                    "north": EUROPE_BOUNDS[3],
                },
                "fallback": "Global 110m geometry remains active if the regional derivative fails",
            },
            "cloud_texture": "1024px mobile and 2048px desktop transparent WebP",
            "poster": "1280px darkened WebP crop",
            "ktx2": "BLOCKED_NO_PINNED_ENCODER",
        },
    }
    PROVENANCE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "assets": len(assets)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
