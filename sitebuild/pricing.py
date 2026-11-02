"""Turn the season plan in site.json into everything that shows a price.

Prices live once in site.json. The table, the closure note, the price FAQ answer,
the JSON-LD priceRange and prices.json (which the weekly pricing check reads) are
all derived from it, so they can't disagree.
"""

import json
from dataclasses import dataclass
from datetime import date, timedelta
from string import Formatter

from sitebuild.models import FaqItem, PageContent, PricesCopy, Pricing, SiteConfig

PLAN_FILE = "prices.json"

PRICE_TEMPLATE_FIELDS: dict[str, set[str]] = {
    "title": {"year"},
    "price_format": {"price"},
    "nights_format": {"nights"},
    "day_format": {"day", "month"},
    "note": {"guests"},
    "closed_note": {"closed_from", "closed_to"},
    "faq_answer": {"year", "min_price", "max_price", "min_nights", "max_nights"},
}


@dataclass(frozen=True)
class Span:
    """Consecutive nights with the same price and minimum stay."""

    start: date
    end: date
    price: int
    min_nights: int


@dataclass(frozen=True)
class SeasonRow:
    dates: str
    price: str
    stay: str


def placeholders(template: str) -> set[str]:
    return {name for _, name, _, _ in Formatter().parse(template) if name}


def template_problems(copy: PricesCopy) -> list[str]:
    """Placeholders each translated template must use, and only those."""
    problems = []
    for field, expected in PRICE_TEMPLATE_FIELDS.items():
        found = placeholders(getattr(copy, field))
        if found != expected:
            problems.append(
                f"prices.{field}: expected {{{', '.join(sorted(expected))}}}, "
                f"found {{{', '.join(sorted(found))}}}"
            )
    return problems


def format_day(day: date, copy: PricesCopy) -> str:
    return copy.day_format.format(day=day.day, month=copy.months[day.month - 1])


def format_price(amount: int, copy: PricesCopy) -> str:
    return copy.price_format.format(price=amount)


def nightly_plan(pricing: Pricing, year: int) -> list[tuple[date, int, int]]:
    """Every open night of the year with its price and minimum stay, exceptions applied."""
    nights = []
    for start, end, season in pricing.season_dates(year):
        night = start
        while night <= end:
            exception = pricing.exception_on(night)
            rule = exception or season
            nights.append((night, rule.price, rule.min_nights))
            night += timedelta(days=1)
    return nights


def spans(pricing: Pricing, year: int) -> list[Span]:
    result: list[Span] = []
    for night, price, min_nights in nightly_plan(pricing, year):
        last = result[-1] if result else None
        if (
            last
            and last.end + timedelta(days=1) == night
            and (last.price, last.min_nights) == (price, min_nights)
        ):
            result[-1] = Span(last.start, night, price, min_nights)
        else:
            result.append(Span(night, night, price, min_nights))
    return result


def season_rows(pricing: Pricing, copy: PricesCopy) -> list[SeasonRow]:
    return [
        SeasonRow(
            dates=f"{format_day(span.start, copy)} – {format_day(span.end, copy)}",
            price=format_price(span.price, copy),
            stay=copy.nights_format.format(nights=span.min_nights),
        )
        for span in spans(pricing, pricing.shown_year)
    ]


def closure(pricing: Pricing) -> tuple[date, date]:
    """From the day after the last season to the day before the first one next year."""
    seasons = pricing.season_dates(pricing.shown_year)
    closed_from = seasons[-1][1] + timedelta(days=1)
    first_start = seasons[0][0]
    closed_to = first_start.replace(year=first_start.year + 1) - timedelta(days=1)
    return closed_from, closed_to


def price_range(pricing: Pricing) -> tuple[int, int]:
    """Cheapest and dearest night of the year the pages show."""
    prices = [span.price for span in spans(pricing, pricing.shown_year)]
    return min(prices), max(prices)


def stay_range(pricing: Pricing) -> tuple[int, int]:
    nights = [span.min_nights for span in spans(pricing, pricing.shown_year)]
    return min(nights), max(nights)


def closed_note(pricing: Pricing, copy: PricesCopy) -> str:
    closed_from, closed_to = closure(pricing)
    return copy.closed_note.format(
        closed_from=format_day(closed_from, copy),
        closed_to=format_day(closed_to, copy),
    )


def price_faq(pricing: Pricing, copy: PricesCopy) -> FaqItem:
    low, high = price_range(pricing)
    min_nights, max_nights = stay_range(pricing)
    return FaqItem(
        question=copy.faq_question,
        answer=copy.faq_answer.format(
            year=pricing.shown_year,
            min_price=format_price(low, copy),
            max_price=format_price(high, copy),
            min_nights=min_nights,
            max_nights=max_nights,
        ),
    )


def faq_items(site: SiteConfig, page: PageContent) -> list[FaqItem]:
    """The page's FAQ plus the price question, placed just before the last (booking) item."""
    items = list(page.faq.items)
    items.insert(len(items) - 1, price_faq(site.pricing, page.prices))
    return items


def price_range_label(pricing: Pricing) -> str:
    low, high = price_range(pricing)
    return f"€{low}–€{high}"


def plan_document(site: SiteConfig) -> dict:
    """The public, machine-readable plan: what the weekly pricing check compares
    Airbnb's calendar with, and what AI agents can read without parsing HTML."""
    pricing = site.pricing
    closed_from, closed_to = closure(pricing)
    return {
        "schema_version": 1,
        "about": (
            f"Season prices of {site.name} in euro per night for the whole villa "
            "(up to {guests} guests), before Airbnb fees. Seasons repeat every year; "
            "exceptions apply to their dates only. Generated from src/site.json."
        ).format(guests=site.facts.guests),
        "booking_url": f"https://www.airbnb.com/rooms/{site.airbnb_listing_id}",
        "currency": "EUR",
        "shown_year": pricing.shown_year,
        "base_price": pricing.base_price,
        "seasons": [season.model_dump() for season in pricing.seasons],
        "exceptions": [
            exception.model_dump(mode="json")
            for exception in sorted(pricing.exceptions, key=lambda item: item.start)
        ],
        "closed_days": list(pricing.closed_days),
        "closure": {"from": closed_from.strftime("%m-%d"), "to": closed_to.strftime("%m-%d")},
    }


def plan_json(site: SiteConfig) -> str:
    return json.dumps(plan_document(site), indent=2, ensure_ascii=False) + "\n"
