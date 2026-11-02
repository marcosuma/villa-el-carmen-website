from datetime import date

import pytest
from pydantic import ValidationError

from sitebuild.models import Pricing, Season
from sitebuild.pricing import (
    closed_note,
    closure,
    faq_items,
    price_faq,
    price_range,
    price_range_label,
    season_rows,
    template_problems,
)


def two_seasons(**overrides):
    seasons = [
        Season(start="04-01", end="05-31", price=420, min_nights=3),
        Season(start="06-01", end="10-06", price=740, min_nights=6),
    ]
    return Pricing(year=overrides.get("year", 2027), seasons=overrides.get("seasons", seasons))


def test_pricing_rejects_overlapping_seasons():
    with pytest.raises(ValidationError, match="overlap"):
        two_seasons(
            seasons=[
                Season(start="04-01", end="06-05", price=420, min_nights=3),
                Season(start="06-01", end="10-06", price=740, min_nights=6),
            ]
        )


def test_pricing_rejects_a_season_that_ends_before_it_starts():
    with pytest.raises(ValidationError, match="ends before"):
        two_seasons(seasons=[Season(start="05-31", end="04-01", price=420, min_nights=3)])


def test_pricing_rejects_impossible_dates():
    with pytest.raises(ValidationError, match="invalid season date"):
        two_seasons(seasons=[Season(start="02-30", end="03-01", price=420, min_nights=3)])


def test_closure_runs_from_after_the_last_season_to_before_the_first_next_year():
    assert closure(two_seasons()) == (date(2027, 10, 7), date(2028, 3, 31))


def test_price_range_and_label_use_the_cheapest_and_dearest_season():
    assert price_range(two_seasons()) == (420, 740)
    assert price_range_label(two_seasons()) == "€420–€740"


def test_season_rows_format_dates_prices_and_stays_per_language(pages):
    italian = season_rows(two_seasons(), pages["it"].prices)
    german = season_rows(two_seasons(), pages["de"].prices)

    assert (italian[0].dates, italian[0].price, italian[0].stay) == (
        "1 apr – 31 mag",
        "420 €",
        "3 notti",
    )
    assert german[1].dates == "1. Juni – 6. Okt."
    assert season_rows(two_seasons(), pages["en"].prices)[1].price == "€740"


def test_closed_note_names_the_closure_dates(pages):
    assert closed_note(two_seasons(), pages["en"].prices) == (
        "The villa is closed from 7 Oct to 31 Mar."
    )


def test_price_faq_is_filled_from_the_seasons(pages):
    item = price_faq(two_seasons(), pages["en"].prices)

    assert item.question == "How much does the villa cost per night?"
    assert "In 2027 the whole villa costs from €420 to €740 per night" in item.answer
    assert "minimum stay of 3 to 6 nights" in item.answer


def test_faq_items_put_the_price_question_before_the_booking_question(site, pages):
    items = faq_items(site, pages["en"])

    assert len(items) == len(pages["en"].faq.items) + 1
    assert items[-2].question == pages["en"].prices.faq_question
    assert items[-1] == pages["en"].faq.items[-1]


def test_template_problems_reports_missing_and_unknown_placeholders(pages):
    broken = pages["en"].prices.model_copy(
        update={"title": "Prices", "nights_format": "{nights} nights, {guests} guests"}
    )

    problems = template_problems(broken)

    assert any(problem.startswith("prices.title") for problem in problems)
    assert any(problem.startswith("prices.nights_format") for problem in problems)
    assert len(problems) == 2


@pytest.mark.parametrize("code", ["en", "it", "de", "fr", "es"])
def test_every_language_fills_the_price_templates(pages, code):
    assert template_problems(pages[code].prices) == []


def test_site_prices_match_the_2027_plan(site):
    plan = [(s.start, s.end, s.price, s.min_nights) for s in site.pricing.seasons]

    assert site.pricing.year == 2027
    assert plan[0] == ("04-01", "05-31", 420, 3)
    assert plan[-1] == ("10-01", "10-06", 420, 3)
    assert max(price for *_, price, _ in plan) == 740
