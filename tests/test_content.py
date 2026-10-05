import pytest

from sitebuild.build import PAGE_IMAGES
from sitebuild.content import check_page, check_same_shape, load_images

LANGUAGES = ["en", "it", "de", "fr", "es"]


def test_every_language_has_content(pages):
    assert sorted(pages) == sorted(LANGUAGES)


@pytest.mark.parametrize("code", LANGUAGES)
def test_titles_fit_in_search_results(pages, code):
    assert len(pages[code].meta.title) <= 60


@pytest.mark.parametrize("code", LANGUAGES)
def test_descriptions_are_search_snippet_length(pages, code):
    assert 120 <= len(pages[code].meta.description) <= 160


@pytest.mark.parametrize("code", LANGUAGES)
def test_titles_mention_trullo_pool_and_ostuni(pages, code):
    title = pages[code].meta.title.lower()
    assert "trullo" in title and "ostuni" in title
    assert any(word in title for word in ("pool", "piscina", "piscine"))


@pytest.mark.parametrize("code", LANGUAGES)
def test_page_passes_cross_checks(site, pages, code):
    assert check_page(code, pages[code], site, load_images(), PAGE_IMAGES) == []


def test_all_languages_have_the_same_shape(pages):
    assert check_same_shape(pages) == []


def test_check_page_reports_missing_alt_text(site, pages):
    page = pages["en"].model_copy(update={"alts": {}})
    problems = check_page("en", page, site, load_images(), PAGE_IMAGES)
    assert any("missing alt text" in problem for problem in problems)


def test_check_same_shape_reports_faq_mismatch(pages):
    shorter_faq = pages["it"].faq.model_copy(update={"items": pages["it"].faq.items[:-1]})
    broken = {"en": pages["en"], "it": pages["it"].model_copy(update={"faq": shorter_faq})}
    assert any("FAQ items" in problem for problem in check_same_shape(broken))


@pytest.mark.parametrize("code", LANGUAGES)
def test_copy_does_not_place_the_villa_in_valle_d_itria(pages, code):
    assert "valle d'itria" not in pages[code].about.paragraphs[0].lower()
