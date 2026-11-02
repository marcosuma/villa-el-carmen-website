import json
from pathlib import Path

import pytest

from sitebuild import ROOT
from sitebuild.build import image_attributes
from sitebuild.models import ImageInfo
from tests.helpers import parse

LANGUAGE_FILES = {
    "en": "index.html",
    "it": "it/index.html",
    "de": "de/index.html",
    "fr": "fr/index.html",
    "es": "es/index.html",
}
INDEXNOW_KEY = json.loads((ROOT / "src" / "site.json").read_text(encoding="utf-8"))["indexnow_key"]
GENERATED = [*LANGUAGE_FILES.values(), "404.html", "robots.txt", f"{INDEXNOW_KEY}.txt"]


def read_page(root: Path, code: str):
    return parse((root / LANGUAGE_FILES[code]).read_text(encoding="utf-8"))


def test_image_attributes_build_responsive_srcset():
    info = ImageInfo(slug="pool-day", width=1600, height=1200, widths=[480, 960, 1600])
    attributes = image_attributes(info)
    assert attributes["src"] == "/assets/img/pool-day-960.webp"
    assert attributes["srcset"].count("w,") == 2
    assert (attributes["width"], attributes["height"]) == (960, 720)
    assert attributes["full"] == "/assets/img/pool-day-1600.webp"


@pytest.mark.parametrize("code", LANGUAGE_FILES)
def test_page_declares_its_language_and_has_one_h1(built_site, code):
    page = read_page(built_site, code)
    assert page.html_lang == code
    assert page.h1_count == 1


@pytest.mark.parametrize("code", LANGUAGE_FILES)
def test_page_has_title_description_and_self_canonical(built_site, site, pages, code):
    page = read_page(built_site, code)
    assert page.title == pages[code].meta.title
    assert page.meta["description"] == pages[code].meta.description
    canonical = [link["href"] for link in page.links if link.get("rel") == "canonical"]
    assert canonical == [site.base_url + site.language(code).path]


def hreflang_map(page):
    return {
        link["hreflang"]: link["href"]
        for link in page.links
        if link.get("rel") == "alternate" and "hreflang" in link
    }


def test_hreflang_links_are_identical_and_reciprocal_on_every_page(built_site):
    maps = [hreflang_map(read_page(built_site, code)) for code in LANGUAGE_FILES]
    assert all(mapping == maps[0] for mapping in maps)
    assert set(maps[0]) == {"en", "it", "de", "fr", "es", "x-default"}


@pytest.mark.parametrize("code", LANGUAGE_FILES)
def test_airbnb_links_use_the_local_domain(built_site, site, code):
    page = read_page(built_site, code)
    airbnb = {a["href"] for a in page.anchors if "airbnb" in a.get("href", "")}
    assert airbnb == {f"https://{site.language(code).airbnb_domain}/rooms/1205785008353242688"}


@pytest.mark.parametrize("code", LANGUAGE_FILES)
def test_footer_shows_cin_and_cis(built_site, code):
    html = (built_site / LANGUAGE_FILES[code]).read_text(encoding="utf-8")
    assert "IT074017C200100796" in html
    assert "BR07401791000058399" in html


@pytest.mark.parametrize("code", LANGUAGE_FILES)
def test_json_ld_is_valid(built_site, code):
    page = read_page(built_site, code)
    data = json.loads("".join(page.json_ld))
    assert data["@context"] == "https://schema.org"


@pytest.mark.parametrize("code", LANGUAGE_FILES)
def test_every_local_asset_exists(built_site, code):
    page = read_page(built_site, code)
    local = {asset for asset in page.assets if asset.startswith("/")}
    missing = sorted(asset for asset in local if not (ROOT / asset.lstrip("/")).is_file())
    assert missing == []


def test_language_switcher_links_to_every_language(built_site):
    page = read_page(built_site, "it")
    switch = {a["href"] for a in page.anchors if a.get("hreflang")}
    assert switch == {"/", "/it/", "/de/", "/fr/", "/es/"}


def test_not_found_page_is_not_indexed(built_site):
    page = parse((built_site / "404.html").read_text(encoding="utf-8"))
    assert page.meta["robots"].startswith("noindex")


@pytest.mark.parametrize("name", GENERATED)
def test_committed_output_matches_sources(built_site, name):
    """Fails when src/ changed but `python -m sitebuild.build` was not re-run."""
    committed = (ROOT / name).read_text(encoding="utf-8")
    fresh = (built_site / name).read_text(encoding="utf-8")
    assert committed.replace(str(2026), "YEAR") == fresh.replace(str(2026), "YEAR")


def vercel_rules() -> tuple[set[str], set[str]]:
    """(top-level entries re-included, sub-paths excluded again) from .vercelignore."""
    lines = (ROOT / ".vercelignore").read_text(encoding="utf-8").splitlines()
    rules = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
    allowed = {rule[1:] for rule in rules if rule.startswith("!")}
    excluded = {rule for rule in rules if not rule.startswith(("!", "/"))}
    return allowed, excluded


@pytest.mark.parametrize("code", LANGUAGE_FILES)
def test_vercel_deploys_every_asset_a_page_uses(built_site, code):
    allowed, excluded = vercel_rules()
    page = read_page(built_site, code)
    local = {asset.lstrip("/") for asset in page.assets if asset.startswith("/")}
    not_deployed = sorted(
        asset
        for asset in local
        if asset.split("/")[0] not in allowed or any(asset.startswith(f"{e}/") for e in excluded)
    )
    assert not_deployed == []


@pytest.mark.parametrize("code", LANGUAGE_FILES)
def test_page_lists_every_season_with_price_and_minimum_stay(built_site, site, code):
    html = (built_site / LANGUAGE_FILES[code]).read_text(encoding="utf-8")
    table = html[html.index('class="price-table"') : html.index("</table>")]

    assert table.count("<tr><td>") == len(site.pricing.seasons)
    assert "740" in table and "420" in table


@pytest.mark.parametrize("code", LANGUAGE_FILES)
def test_page_faq_includes_the_price_question(built_site, pages, code):
    html = (built_site / LANGUAGE_FILES[code]).read_text(encoding="utf-8")

    assert html.count(f"<summary>{pages[code].prices.faq_question}</summary>") == 1


def test_build_writes_the_indexnow_key_file(built_site, site):
    key_file = built_site / f"{site.indexnow_key}.txt"

    assert key_file.read_text(encoding="utf-8") == site.indexnow_key


def test_vercel_deploys_the_indexnow_key_file(site):
    allowed, _ = vercel_rules()

    assert f"{site.indexnow_key}.txt" in allowed


def test_vercel_keeps_build_sources_off_the_site():
    allowed, _ = vercel_rules()
    assert {"index.html", "404.html", "robots.txt", "sitemap.xml"} <= allowed
    assert not allowed & {"src", "sitebuild", "tests", "tools", "docs", "README.md", ".github"}
