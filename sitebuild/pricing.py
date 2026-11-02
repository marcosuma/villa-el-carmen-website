"""Turn the season plan in site.json into the text shown on each language page.

Prices live once in site.json; the table, the closure note, the price FAQ answer and
the JSON-LD priceRange are all derived from it so they can't disagree.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from string import Formatter

from sitebuild.models import FaqItem, PageContent, PricesCopy, Pricing, SiteConfig

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


def season_rows(pricing: Pricing, copy: PricesCopy) -> list[SeasonRow]:
    return [
        SeasonRow(
            dates=f"{format_day(start, copy)} – {format_day(end, copy)}",
            price=format_price(season.price, copy),
            stay=copy.nights_format.format(nights=season.min_nights),
        )
        for start, end, season in pricing.season_dates()
    ]


def closure(pricing: Pricing) -> tuple[date, date]:
    """From the day after the last season to the day before the first one next year."""
    spans = pricing.season_dates()
    closed_from = spans[-1][1] + timedelta(days=1)
    first_start = spans[0][0]
    closed_to = first_start.replace(year=first_start.year + 1) - timedelta(days=1)
    return closed_from, closed_to


def price_range(pricing: Pricing) -> tuple[int, int]:
    prices = [season.price for season in pricing.seasons]
    return min(prices), max(prices)


def stay_range(pricing: Pricing) -> tuple[int, int]:
    nights = [season.min_nights for season in pricing.seasons]
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
            year=pricing.year,
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
