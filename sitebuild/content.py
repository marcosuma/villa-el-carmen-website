"""Load and cross-check the site configuration and the copy for every language."""

import json
from pathlib import Path

from pydantic import ValidationError

from sitebuild import ROOT
from sitebuild.models import ImageInfo, PageContent, SiteConfig

SRC = ROOT / "src"


class ContentError(Exception):
    pass


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ContentError(f"missing file: {path}") from error
    except json.JSONDecodeError as error:
        raise ContentError(f"invalid JSON in {path}: {error}") from error


def load_site(path: Path = SRC / "site.json") -> SiteConfig:
    try:
        return SiteConfig.model_validate(read_json(path))
    except ValidationError as error:
        raise ContentError(f"{path}: {error}") from error


def load_images(path: Path = SRC / "images.generated.json") -> dict[str, ImageInfo]:
    raw = read_json(path)
    if not isinstance(raw, list):
        raise ContentError(f"{path}: expected a list")
    images = [ImageInfo.model_validate(item) for item in raw]
    return {image.slug: image for image in images}


def load_page(code: str, directory: Path = SRC / "content") -> PageContent:
    path = directory / f"{code}.json"
    try:
        return PageContent.model_validate(read_json(path))
    except ValidationError as error:
        raise ContentError(f"{path}: {error}") from error


def required_alt_slugs(site: SiteConfig, page_slugs: set[str]) -> set[str]:
    return set(site.gallery) | page_slugs


def check_page(
    code: str,
    page: PageContent,
    site: SiteConfig,
    images: dict[str, ImageInfo],
    page_slugs: set[str],
) -> list[str]:
    """Return human-readable problems; an empty list means the page can be built."""
    problems = []
    needed = required_alt_slugs(site, page_slugs)
    missing_alts = sorted(needed - set(page.alts))
    if missing_alts:
        problems.append(f"{code}: missing alt text for {', '.join(missing_alts)}")
    unknown_images = sorted(needed - set(images))
    if unknown_images:
        problems.append(f"{code}: no generated image for {', '.join(unknown_images)}")
    distance_keys = {distance.key for distance in site.distances}
    missing_labels = sorted(distance_keys - set(page.location.distance_labels))
    if missing_labels:
        problems.append(f"{code}: missing distance label for {', '.join(missing_labels)}")
    return problems


def check_same_shape(pages: dict[str, PageContent]) -> list[str]:
    """Every language must have the same number of FAQ items, beaches and alts."""
    problems = []
    reference_code, reference = next(iter(pages.items()))
    for code, page in pages.items():
        if len(page.faq.items) != len(reference.faq.items):
            problems.append(
                f"{code}: {len(page.faq.items)} FAQ items, {reference_code} has "
                f"{len(reference.faq.items)}"
            )
        if set(page.alts) != set(reference.alts):
            problems.append(f"{code}: alt slugs differ from {reference_code}")
    return problems
