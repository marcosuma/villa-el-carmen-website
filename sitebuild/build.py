"""Render every language page, the 404 page, sitemap.xml and robots.txt.

Run after editing src/: ``python -m sitebuild.build``. The generated files are
committed; Vercel serves them as plain static files.
"""

import sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from sitebuild import ROOT
from sitebuild.content import (
    ContentError,
    check_page,
    check_same_shape,
    load_images,
    load_page,
    load_site,
)
from sitebuild.models import ImageInfo, Language, PageContent, SiteConfig
from sitebuild.seo import (
    airbnb_url,
    alternates,
    format_duration,
    page_url,
    robots_txt,
    sitemap_xml,
    structured_data,
)

TEMPLATES = ROOT / "src" / "templates"
IMAGE_URL_PREFIX = "/assets/img"

# Images placed by the template outside the gallery; each needs alt text in every language.
PAGE_IMAGES = {
    "trullo-interior",
    "lamia-dining",
    "pool-day",
    "olive-grove",
    "workspace-olive-view",
    "olive-oil-mill",
    "aperitivo",
    "outdoor-dining",
    "orecchiette",
    "countryside-aerial",
}


def make_environment() -> Environment:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html", "j2"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.globals["zip"] = zip
    return environment


def image_attributes(info: ImageInfo, preferred_width: int = 960) -> dict:
    widths = info.widths
    src_width = min(widths, key=lambda width: abs(width - preferred_width))
    height = round(info.height * src_width / info.width)
    return {
        "src": f"{IMAGE_URL_PREFIX}/{info.slug}-{src_width}.webp",
        "srcset": ", ".join(f"{IMAGE_URL_PREFIX}/{info.slug}-{w}.webp {w}w" for w in widths),
        "width": src_width,
        "height": height,
        "full": f"{IMAGE_URL_PREFIX}/{info.slug}-{widths[-1]}.webp",
    }


def output_path(language: Language, root: Path = ROOT) -> Path:
    return root / language.path.strip("/") / "index.html"


def page_context(
    site: SiteConfig,
    language: Language,
    page: PageContent,
    images: dict[str, ImageInfo],
    today: date,
) -> dict:
    return {
        "site": site,
        "lang": language,
        "page": page,
        "canonical": page_url(site, language),
        "alternates": alternates(site),
        "airbnb": airbnb_url(site, language),
        "img": {slug: image_attributes(info) for slug, info in images.items()},
        "distances": [
            (page.location.distance_labels[d.key], format_duration(d.minutes, page))
            for d in site.distances
        ],
        "other_languages": [other for other in site.languages if other.code != language.code],
        "structured_data": structured_data(site, language, page),
        "year": today.year,
    }


def load_all() -> tuple[SiteConfig, dict[str, ImageInfo], dict[str, PageContent]]:
    site = load_site()
    images = load_images()
    pages = {language.code: load_page(language.code) for language in site.languages}
    problems = check_same_shape(pages)
    for code, page in pages.items():
        problems += check_page(code, page, site, images, PAGE_IMAGES)
    if problems:
        raise ContentError("\n".join(problems))
    return site, images, pages


def build(root: Path = ROOT, today: date | None = None) -> list[Path]:
    today = today or date.today()
    site, images, pages = load_all()
    environment = make_environment()
    page_template = environment.get_template("page.html.j2")
    written = []
    for language in site.languages:
        context = page_context(site, language, pages[language.code], images, today)
        path = output_path(language, root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(page_template.render(context), encoding="utf-8")
        written.append(path)

    default = site.language(site.default_language)
    not_found = environment.get_template("404.html.j2").render(
        page_context(site, default, pages[default.code], images, today) | {"pages": pages}
    )
    for name, text in (
        ("404.html", not_found),
        ("sitemap.xml", sitemap_xml(site, today)),
        ("robots.txt", robots_txt(site)),
    ):
        path = root / name
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    try:
        written = build()
    except ContentError as error:
        print(f"Build failed:\n{error}", file=sys.stderr)
        return 1
    for path in written:
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
