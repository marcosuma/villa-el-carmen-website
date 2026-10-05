from pathlib import Path

import pytest
from PIL import Image

from sitebuild.media import (
    ImageVariant,
    MediaError,
    crop_to_ratio,
    ffmpeg_poster_command,
    ffmpeg_video_command,
    fit_within,
    image_info,
    scaled_height,
    square_icon,
    target_widths,
    variant_path,
    write_icons,
    write_logo,
)

VIDEO = {
    "source": "assets/videos/in.mov",
    "output": "assets/video/out.mp4",
    "poster": "assets/img/poster.webp",
    "width": 1280,
    "crf": 32,
    "fps": 24,
    "duration_seconds": 24,
    "poster_at_seconds": 1.0,
}


def test_target_widths_keeps_configured_widths_below_original():
    assert target_widths(4032, [480, 960, 1600]) == [480, 960, 1600]


def test_target_widths_never_upscales_small_images():
    assert target_widths(1200, [480, 960, 1600]) == [480, 960, 1200]


def test_target_widths_for_tiny_image_uses_original_width():
    assert target_widths(300, [480, 960, 1600]) == [300]


def test_target_widths_rejects_invalid_width():
    with pytest.raises(MediaError):
        target_widths(0, [480])


def test_scaled_height_keeps_aspect_ratio():
    assert scaled_height(4032, 3024, 960) == 720


def test_variant_path_names_file_by_slug_and_width(tmp_path):
    assert variant_path("pool-day", 960, tmp_path) == tmp_path / "pool-day-960.webp"


def test_crop_to_ratio_returns_exact_size():
    image = Image.new("RGB", (4032, 3024))
    assert crop_to_ratio(image, 1200, 630).size == (1200, 630)


def test_image_info_reports_largest_variant():
    variants = [ImageVariant(480, 360, Path("a")), ImageVariant(960, 720, Path("b"))]
    assert image_info("x", variants) == {
        "slug": "x",
        "width": 960,
        "height": 720,
        "widths": [480, 960],
    }


def test_video_command_trims_scales_and_drops_audio():
    command = ffmpeg_video_command(VIDEO)
    joined = " ".join(command)
    assert "-t 24" in joined
    assert "scale=1280:-2,fps=24" in joined
    assert "-an" in command
    assert "+faststart" in command
    assert command[-1].endswith("assets/video/out.mp4")


def test_poster_command_grabs_single_frame_as_webp():
    command = ffmpeg_poster_command(VIDEO)
    assert command[command.index("-frames:v") + 1] == "1"
    assert command[-1].endswith("poster.webp")


def test_fit_within_scales_the_longest_side_to_the_box():
    assert fit_within(512, 380, 96) == (96, 71)
    assert fit_within(380, 512, 96) == (71, 96)


def test_fit_within_never_upscales():
    assert fit_within(40, 30, 96) == (40, 30)


def test_square_icon_centres_a_wide_icon_on_a_transparent_square():
    icon = Image.new("RGBA", (200, 100), (0, 0, 0, 255))
    square = square_icon(icon, 96)
    assert square.size == (96, 96)
    assert square.getpixel((0, 0))[3] == 0
    assert square.getpixel((48, 48))[3] == 255


def test_write_icons_writes_square_webp_files(tmp_path, monkeypatch):
    monkeypatch.setattr("sitebuild.media.ROOT", tmp_path)
    (tmp_path / "icons").mkdir()
    Image.new("RGBA", (512, 380), (10, 20, 30, 255)).save(tmp_path / "icons" / "bed.png")
    written = write_icons(
        {"source_dir": "icons", "output_dir": "icons/web", "size": 96, "names": ["bed"]}
    )
    assert written == [tmp_path / "icons" / "web" / "bed.webp"]
    with Image.open(written[0]) as result:
        assert (result.format, result.size) == ("WEBP", (96, 96))


def test_write_logo_writes_square_webp_and_favicon(tmp_path, monkeypatch):
    monkeypatch.setattr("sitebuild.media.ROOT", tmp_path)
    (tmp_path / "web").mkdir()
    Image.new("RGBA", (400, 300), (200, 190, 140, 255)).save(tmp_path / "logo.png")
    webp, favicon = write_logo(
        {
            "source": "logo.png",
            "size": 180,
            "web_size": 96,
            "webp": "web/logo.webp",
            "favicon": "web/favicon.png",
        }
    )
    with Image.open(webp) as small, Image.open(favicon) as large:
        assert small.size == (96, 96)
        assert large.size == (180, 180)
