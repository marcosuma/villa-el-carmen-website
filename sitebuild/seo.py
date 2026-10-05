"""URLs, hreflang alternates, structured data and the sitemap."""

import json
from datetime import date
from xml.sax.saxutils import escape

from sitebuild.models import Language, PageContent, SiteConfig

X_DEFAULT = "x-default"


def page_url(site: SiteConfig, language: Language) -> str:
    return site.base_url + language.path


def airbnb_url(site: SiteConfig, language: Language) -> str:
    return f"https://{language.airbnb_domain}/rooms/{site.airbnb_listing_id}"


def alternates(site: SiteConfig) -> list[tuple[str, str]]:
    """(hreflang, url) pairs for every language plus x-default, identical on every page."""
    pairs = [(language.code, page_url(site, language)) for language in site.languages]
    default = site.language(site.default_language)
    pairs.append((X_DEFAULT, page_url(site, default)))
    return pairs


def format_duration(minutes: int, page: PageContent) -> str:
    formats = page.location.time_formats
    if minutes < 60:
        return formats.minutes.format(m=minutes)
    hours, rest = divmod(minutes, 60)
    if rest == 0:
        return formats.hours.format(h=hours)
    return formats.hours_minutes.format(h=hours, m=rest)


def lodging_schema(site: SiteConfig, language: Language, page: PageContent) -> dict:
    url = page_url(site, language)
    facts = site.facts
    amenities = [
        page.facts.pool,
        page.facts.wifi,
        page.facts.air_conditioning,
        page.facts.barbecue,
        page.facts.parking,
    ]
    return {
        "@type": "LodgingBusiness",
        "@id": f"{site.base_url}/#villa",
        "name": site.name,
        "url": url,
        "description": page.meta.description,
        "image": [site.base_url + site.og_image.path],
        "email": site.email,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": site.address.locality,
            "postalCode": site.address.postal_code,
            "addressRegion": site.address.region,
            "addressCountry": site.address.country,
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": site.geo.latitude,
            "longitude": site.geo.longitude,
        },
        "hasMap": site.google_maps_url,
        "checkinTime": facts.checkin_time,
        "checkoutTime": facts.checkout_time,
        "numberOfRooms": facts.bedrooms,
        "petsAllowed": False,
        "amenityFeature": [
            {"@type": "LocationFeatureSpecification", "name": name, "value": True}
            for name in amenities
        ],
        "containsPlace": {
            "@type": "House",
            "numberOfBedrooms": facts.bedrooms,
            "numberOfBathroomsTotal": facts.bathrooms,
            "occupancy": {"@type": "QuantitativeValue", "maxValue": facts.guests},
        },
        "identifier": [
            {"@type": "PropertyValue", "propertyID": "CIN", "value": site.cin},
            {"@type": "PropertyValue", "propertyID": "CIS", "value": site.cis},
        ],
        "sameAs": [airbnb_url(site, site.language("en")), site.instagram_url],
    }


def faq_schema(page: PageContent) -> dict:
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item.question,
                "acceptedAnswer": {"@type": "Answer", "text": item.answer},
            }
            for item in page.faq.items
        ],
    }


def structured_data(site: SiteConfig, language: Language, page: PageContent) -> str:
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{site.base_url}/#website",
                "url": site.base_url + "/",
                "name": site.name,
                "inLanguage": [lang.code for lang in site.languages],
            },
            lodging_schema(site, language, page),
            faq_schema(page),
        ],
    }
    # "</" inside a JSON string would close the <script> element early.
    return json.dumps(graph, ensure_ascii=False, indent=2).replace("</", "<\\/")


def sitemap_xml(site: SiteConfig, lastmod: date) -> str:
    links = "".join(
        f'\n    <xhtml:link rel="alternate" hreflang="{code}" href="{escape(url)}"/>'
        for code, url in alternates(site)
    )
    entries = "".join(
        f"\n  <url>\n    <loc>{escape(page_url(site, language))}</loc>"
        f"\n    <lastmod>{lastmod.isoformat()}</lastmod>{links}\n  </url>"
        for language in site.languages
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">'
        f"{entries}\n</urlset>\n"
    )


def robots_txt(site: SiteConfig) -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {site.base_url}/sitemap.xml\n"
