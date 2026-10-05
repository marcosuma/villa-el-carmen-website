"""Turn the original photos and hero video into web-sized assets.

Run once after adding or replacing a photo: ``python -m sitebuild.media``.
Outputs are committed, so the site itself needs no build step on Vercel.
"""

import json
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

from sitebuild import ROOT

MANIFEST_PATH = ROOT / "src" / "media.json"
IMAGE_INFO_PATH = ROOT / "src" / "images.generated.json"
IMAGE_DIR = ROOT / "assets" / "img"


class MediaError(Exception):
    pass


@dataclass(frozen=True)
class ImageVariant:
    width: int
    height: int
    path: Path


def target_widths(original_width: int, widths: Sequence[int]) -> list[int]:
    """Widths to generate: every configured width below the original, plus the original
    width itself when it is smaller than the largest configured one (no upscaling)."""
    if original_width <= 0:
        raise MediaError(f"invalid image width: {original_width}")
    chosen = sorted({w for w in widths if w < original_width})
    largest = max(widths)
    if original_width <= largest and original_width not in chosen:
        chosen.append(original_width)
    if not chosen:
        chosen = [min(original_width, largest)]
    return sorted(chosen)


def scaled_height(original_width: int, original_height: int, width: int) -> int:
    return max(1, round(original_height * width / original_width))


def variant_path(slug: str, width: int, directory: Path = IMAGE_DIR) -> Path:
    return directory / f"{slug}-{width}.webp"


def load_upright_rgb(source: Path) -> Image.Image:
    if not source.is_file():
        raise MediaError(f"missing source image: {source}")
    with Image.open(source) as opened:
        # exif_transpose applies the camera rotation; converting drops EXIF (and GPS) data.
        return ImageOps.exif_transpose(opened).convert("RGB")


def write_variants(
    slug: str, source: Path, widths: Sequence[int], quality: int
) -> list[ImageVariant]:
    image = load_upright_rgb(source)
    variants = []
    for width in target_widths(image.width, widths):
        height = scaled_height(image.width, image.height, width)
        path = variant_path(slug, width)
        image.resize((width, height), Image.Resampling.LANCZOS).save(
            path, "WEBP", quality=quality, method=6
        )
        variants.append(ImageVariant(width, height, path))
    return variants


def crop_to_ratio(image: Image.Image, width: int, height: int) -> Image.Image:
    return ImageOps.fit(image, (width, height), Image.Resampling.LANCZOS, centering=(0.5, 0.55))


def write_og_image(config: dict) -> Path:
    image = load_upright_rgb(ROOT / config["source"])
    output = ROOT / config["output"]
    crop_to_ratio(image, config["width"], config["height"]).save(
        output, "JPEG", quality=82, optimize=True, progressive=True
    )
    return output


def ffmpeg_video_command(config: dict) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(ROOT / config["source"]),
        "-t",
        str(config["duration_seconds"]),
        "-vf",
        f"scale={config['width']}:-2,fps={config['fps']}",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        str(config["crf"]),
        "-profile:v",
        "high",
        "-pix_fmt",
        "yuv420p",
        "-an",
        "-movflags",
        "+faststart",
        str(ROOT / config["output"]),
    ]


def ffmpeg_poster_command(config: dict) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-ss",
        str(config["poster_at_seconds"]),
        "-i",
        str(ROOT / config["source"]),
        "-frames:v",
        "1",
        "-vf",
        f"scale={config['width']}:-2",
        "-c:v",
        "libwebp",
        "-quality",
        "75",
        str(ROOT / config["poster"]),
    ]


def run_ffmpeg(command: list[str]) -> None:
    if shutil.which("ffmpeg") is None:
        raise MediaError("ffmpeg not found: install it to rebuild the hero video")
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise MediaError(f"ffmpeg failed: {completed.stderr.strip()[:300]}")


def image_info(slug: str, variants: Sequence[ImageVariant]) -> dict:
    largest = variants[-1]
    return {
        "slug": slug,
        "width": largest.width,
        "height": largest.height,
        "widths": [variant.width for variant in variants],
    }


def fit_within(width: int, height: int, box: int) -> tuple[int, int]:
    """Largest size with the same aspect ratio that fits in a box x box square."""
    scale = min(box / width, box / height, 1)
    return max(1, round(width * scale)), max(1, round(height * scale))


def square_icon(icon: Image.Image, size: int) -> Image.Image:
    """Scale an icon to fit a size x size square and centre it on a transparent canvas,
    so every icon has the same 1:1 ratio as its width/height attributes."""
    rgba = icon.convert("RGBA")
    resized = rgba.resize(fit_within(*rgba.size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(resized, ((size - resized.width) // 2, (size - resized.height) // 2))
    return canvas


def write_icons(config: dict) -> list[Path]:
    output_dir = ROOT / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name in config["names"]:
        with Image.open(ROOT / config["source_dir"] / f"{name}.png") as icon:
            square = square_icon(icon, config["size"])
        path = output_dir / f"{name}.webp"
        square.save(path, "WEBP", quality=90, method=6)
        written.append(path)
    return written


def write_logo(config: dict) -> list[Path]:
    with Image.open(ROOT / config["source"]) as logo:
        square = ImageOps.fit(logo.convert("RGBA"), (config["size"], config["size"]))
    webp = ROOT / config["webp"]
    favicon = ROOT / config["favicon"]
    square.resize((config["web_size"], config["web_size"]), Image.Resampling.LANCZOS).save(
        webp, "WEBP", quality=90
    )
    square.save(favicon, "PNG", optimize=True)
    return [webp, favicon]


def build_media(manifest_path: Path = MANIFEST_PATH, include_video: bool = True) -> list[dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    infos = []
    for entry in manifest["images"]:
        variants = write_variants(
            entry["slug"], ROOT / entry["source"], manifest["widths"], manifest["quality"]
        )
        infos.append(image_info(entry["slug"], variants))
    IMAGE_INFO_PATH.write_text(json.dumps(infos, indent=2) + "\n", encoding="utf-8")
    write_og_image(manifest["og_image"])
    write_icons(manifest["icons"])
    write_logo(manifest["logo"])
    if include_video:
        video = manifest["video"]
        (ROOT / video["output"]).parent.mkdir(parents=True, exist_ok=True)
        run_ffmpeg(ffmpeg_video_command(video))
        run_ffmpeg(ffmpeg_poster_command(video))
    return infos


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    infos = build_media(include_video="--no-video" not in args)
    print(f"{len(infos)} images written to {IMAGE_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
