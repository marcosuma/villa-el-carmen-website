import json
from datetime import date
from xml.etree import ElementTree

from sitebuild.seo import (
    airbnb_url,
    alternates,
    format_duration,
    page_url,
    robots_txt,
    sitemap_xml,
    structured_data,
)

SITEMAP_NS = {
    "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "x": "http://www.w3.org/1999/xhtml",
}


def test_page_url_uses_language_path(site):
    assert page_url(site, site.language("en")) == "https://elcarmenpuglia.com/"
    assert page_url(site, site.language("de")) == "https://elcarmenpuglia.com/de/"


def test_airbnb_url_uses_local_airbnb_domain(site):
    assert airbnb_url(site, site.language("fr")) == (
        "https://www.airbnb.fr/rooms/1205785008353242688"
    )


def test_alternates_cover_every_language_plus_x_default(site):
    pairs = dict(alternates(site))
    assert set(pairs) == {"en", "it", "de", "fr", "es", "x-default"}
    assert pairs["x-default"] == "https://elcarmenpuglia.com/"


def test_format_duration_minutes_and_hours(pages):
    assert format_duration(25, pages["en"]) == "25 min"
    assert format_duration(60, pages["en"]) == "1 h"
    assert format_duration(90, pages["en"]) == "1 h 30"


def test_format_duration_uses_german_units(pages):
    assert format_duration(25, pages["de"]) == "25 Min."
    assert format_duration(90, pages["de"]) == "1 Std. 30 Min."


def test_structured_data_contains_cin_cis_and_faq(site, pages):
    data = json.loads(structured_data(site, site.language("it"), pages["it"]))
    types = {node["@type"] for node in data["@graph"]}
    assert types == {"WebSite", "LodgingBusiness", "FAQPage"}
    lodging = next(node for node in data["@graph"] if node["@type"] == "LodgingBusiness")
    identifiers = {item["propertyID"]: item["value"] for item in lodging["identifier"]}
    assert identifiers == {"CIN": "IT074017C200100796", "CIS": "BR07401791000058399"}
    assert lodging["containsPlace"]["occupancy"]["maxValue"] == 5
    faq = next(node for node in data["@graph"] if node["@type"] == "FAQPage")
    assert len(faq["mainEntity"]) == len(pages["it"].faq.items)


def test_structured_data_cannot_close_script_tag(site, pages):
    assert "</" not in structured_data(site, site.language("en"), pages["en"])


def test_structured_data_has_no_self_serving_rating(site, pages):
    assert "aggregateRating" not in structured_data(site, site.language("en"), pages["en"])


def test_sitemap_lists_every_language_with_alternates(site):
    tree = ElementTree.fromstring(sitemap_xml(site, date(2026, 10, 5)))
    urls = tree.findall("s:url", SITEMAP_NS)
    assert [u.find("s:loc", SITEMAP_NS).text for u in urls] == [
        "https://elcarmenpuglia.com/",
        "https://elcarmenpuglia.com/it/",
        "https://elcarmenpuglia.com/de/",
        "https://elcarmenpuglia.com/fr/",
        "https://elcarmenpuglia.com/es/",
    ]
    for url in urls:
        assert len(url.findall("x:link", SITEMAP_NS)) == 6
        assert url.find("s:lastmod", SITEMAP_NS).text == "2026-10-05"


def test_robots_allows_crawling_and_points_to_sitemap(site):
    text = robots_txt(site)
    assert "Allow: /" in text
    assert "Disallow" not in text
    assert "Sitemap: https://elcarmenpuglia.com/sitemap.xml" in text
