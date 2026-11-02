import json
from datetime import date

import pytest
from pydantic import ValidationError

from sitebuild.models import PriceException, Pricing, Season
from sitebuild.pricing import (
    closed_note,
    closure,
    faq_items,
    plan_document,
    plan_json,
    price_faq,
    price_range,
    price_range_label,
    season_rows,
    spans,
    template_problems,
)

LOW = Season(start="04-01", end="05-31", price=420, min_nights=3, rule_set="Bassa")
HIGH = Season(start="06-01", end="10-06", price=740, min_nights=6, rule_set="Ferragosto")
EASTER = PriceException(
    start=date(2028, 4, 13),
    end=date(2028, 4, 16),
    price=500,
    min_nights=3,
    rule_set="Spalla",
    reason="Easter",
)


def plan(**overrides):
    fields = {
        "shown_year": 2027,
        "base_price": 500,
        "seasons": [LOW, HIGH],
        "exceptions": [],
        "closed_days": [],
    }
    return Pricing(**(fields | overrides))


def test_pricing_rejects_overlapping_seasons():
    early_high = HIGH.model_copy(update={"start": "05-30"})
    with pytest.raises(ValidationError, match="overlap"):
        plan(seasons=[LOW, early_high])


def test_pricing_rejects_a_season_that_ends_before_it_starts():
    with pytest.raises(ValidationError, match="ends before"):
        plan(seasons=[LOW.model_copy(update={"start": "05-31", "end": "04-01"})])


def test_pricing_rejects_impossible_dates():
    with pytest.raises(ValidationError, match="invalid season date"):
        plan(seasons=[LOW.model_copy(update={"start": "02-30", "end": "03-01"})])


def test_pricing_rejects_an_exception_in_the_winter_closure():
    winter = EASTER.model_copy(update={"start": date(2028, 3, 20), "end": date(2028, 3, 22)})
    with pytest.raises(ValidationError, match="outside the seasons"):
        plan(exceptions=[winter])


def test_pricing_rejects_overlapping_exceptions():
    later = EASTER.model_copy(update={"start": date(2028, 4, 16), "end": date(2028, 4, 18)})
    with pytest.raises(ValidationError, match="exceptions .* overlap"):
        plan(exceptions=[EASTER, later])


def test_pricing_rejects_a_closed_day_already_in_the_closure():
    with pytest.raises(ValidationError, match="already in the winter closure"):
        plan(closed_days=["12-25"])


def test_closure_runs_from_after_the_last_season_to_before_the_first_next_year():
    assert closure(plan()) == (date(2027, 10, 7), date(2028, 3, 31))


def test_spans_split_a_season_around_an_exception():
    pricing = plan(shown_year=2028, exceptions=[EASTER])

    april = [(s.start, s.end, s.price) for s in spans(pricing, 2028)][:3]

    assert april == [
        (date(2028, 4, 1), date(2028, 4, 12), 420),
        (date(2028, 4, 13), date(2028, 4, 16), 500),
        (date(2028, 4, 17), date(2028, 5, 31), 420),
    ]


def test_exceptions_only_change_their_own_year():
    pricing = plan(exceptions=[EASTER])

    assert len(spans(pricing, 2027)) == 2
    assert len(spans(pricing, 2028)) == 4


def test_price_range_and_label_use_the_cheapest_and_dearest_night():
    assert price_range(plan()) == (420, 740)
    assert price_range_label(plan()) == "€420–€740"


def test_season_rows_format_dates_prices_and_stays_per_language(pages):
    italian = season_rows(plan(), pages["it"].prices)
    german = season_rows(plan(), pages["de"].prices)

    assert (italian[0].dates, italian[0].price, italian[0].stay) == (
        "1 apr – 31 mag",
        "420 €",
        "3 notti",
    )
    assert german[1].dates == "1. Juni – 6. Okt."
    assert season_rows(plan(), pages["en"].prices)[1].price == "€740"


def test_season_rows_show_the_exceptions_of_the_shown_year(pages):
    rows = season_rows(plan(shown_year=2028, exceptions=[EASTER]), pages["en"].prices)

    assert [row.price for row in rows] == ["€420", "€500", "€420", "€740"]


def test_closed_note_names_the_closure_dates(pages):
    assert closed_note(plan(), pages["en"].prices) == ("The villa is closed from 7 Oct to 31 Mar.")


def test_price_faq_is_filled_from_the_seasons(pages):
    item = price_faq(plan(), pages["en"].prices)

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


def test_plan_document_carries_everything_the_pricing_check_needs(site):
    document = plan_document(site)

    assert document["shown_year"] == site.pricing.shown_year
    assert document["base_price"] == 500
    assert document["seasons"][0] == {
        "start": "04-01",
        "end": "05-31",
        "price": 420,
        "min_nights": 3,
        "rule_set": "Bassa",
    }
    assert document["exceptions"][0]["start"] == "2028-04-13"
    assert document["closed_days"] == ["08-15", "08-16"]
    assert document["closure"] == {"from": "10-07", "to": "03-31"}


def test_plan_json_round_trips(site):
    assert json.loads(plan_json(site)) == plan_document(site)


def test_site_plan_matches_airbnb(site):
    """The 2027 and 2028 rule sets as set on Airbnb on 2 November 2026."""
    pricing = site.pricing
    table = [(s.start, s.end, s.price, s.min_nights, s.rule_set) for s in pricing.seasons]

    assert table == [
        ("04-01", "05-31", 420, 3, "Bassa"),
        ("06-01", "06-14", 500, 3, "Spalla"),
        ("06-15", "07-09", 580, 4, "Alta"),
        ("07-10", "08-07", 660, 5, "Altissima"),
        ("08-08", "08-22", 740, 6, "Ferragosto"),
        ("08-23", "09-06", 580, 4, "Alta"),
        ("09-07", "09-30", 540, 4, "Settembre"),
        ("10-01", "10-06", 420, 3, "Bassa"),
    ]
    assert [(e.start, e.end, e.price) for e in pricing.exceptions] == [
        (date(2028, 4, 13), date(2028, 4, 16), 500),
        (date(2028, 4, 22), date(2028, 4, 24), 500),
    ]
