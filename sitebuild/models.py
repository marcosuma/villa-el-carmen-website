"""Typed shapes of the site configuration and the per-language copy."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Language(Strict):
    code: str = Field(pattern=r"^[a-z]{2}$")
    path: str = Field(pattern=r"^/([a-z]{2}/)?$")
    locale: str = Field(pattern=r"^[a-z]{2}_[A-Z]{2}$")
    label: str
    short: str
    airbnb_domain: str


class Geo(Strict):
    latitude: float
    longitude: float


class Address(Strict):
    locality: str
    postal_code: str
    province: str
    region: str
    country: str


class Facts(Strict):
    guests: int
    bedrooms: int
    bathrooms: int
    pool_m2: int
    olive_grove_hectares: int
    parking_spaces: int
    checkin_time: str
    checkout_time: str


class Distance(Strict):
    key: str
    minutes: int = Field(gt=0)


class Hero(Strict):
    video: str
    poster: str


class OgImage(Strict):
    path: str
    width: int
    height: int


class SiteConfig(Strict):
    base_url: str = Field(pattern=r"^https://[^/]+$")
    name: str
    default_language: str
    languages: list[Language]
    airbnb_listing_id: str
    email: str
    instagram_url: str
    google_maps_url: str
    cin: str = Field(pattern=r"^IT\d{6}[A-Z0-9]{10}$")
    cis: str
    geo: Geo
    address: Address
    facts: Facts
    distances: list[Distance]
    gallery: list[str]
    hero: Hero
    og_image: OgImage

    @field_validator("languages")
    @classmethod
    def unique_codes(cls, languages: list[Language]) -> list[Language]:
        codes = [language.code for language in languages]
        if len(codes) != len(set(codes)):
            raise ValueError("duplicate language codes")
        return languages

    def language(self, code: str) -> Language:
        for language in self.languages:
            if language.code == code:
                return language
        raise KeyError(code)


class ImageInfo(Strict):
    slug: str
    width: int
    height: int
    widths: list[int]


class Meta(Strict):
    title: str = Field(max_length=65)
    description: str = Field(min_length=70, max_length=160)
    og_title: str
    og_description: str


class Nav(Strict):
    villa: str
    location: str
    faq: str
    book: str
    menu: str
    languages: str


class HeroCopy(Strict):
    h1: str
    subtitle: str
    cta_primary: str
    cta_secondary: str
    video_label: str


class FactLabels(Strict):
    guests: str
    bedrooms: str
    bathrooms: str
    pool: str
    wifi: str
    air_conditioning: str
    barbecue: str
    parking: str


class Section(Strict):
    h2: str
    paragraphs: list[str]


class Card(Strict):
    h3: str
    body: str


class Trullo(Strict):
    h2: str
    intro: str
    cards: list[Card] = Field(min_length=2, max_length=2)


class OliveOil(Strict):
    h2: str
    body: str
    note: str


class Dining(Strict):
    h2: str
    intro: str
    slides: list[Card] = Field(min_length=3, max_length=3)
    previous: str
    next: str


class Gallery(Strict):
    h2: str
    intro: str
    close: str


class TimeFormats(Strict):
    minutes: str
    hours: str
    hours_minutes: str


class Location(Strict):
    h2: str
    intro: str
    distances_title: str
    distance_labels: dict[str, str]
    time_formats: TimeFormats
    beaches_title: str
    beaches: list[str]
    car_note: str
    map_button: str


class FaqItem(Strict):
    question: str
    answer: str


class Faq(Strict):
    h2: str
    items: list[FaqItem] = Field(min_length=5)


class Book(Strict):
    h2: str
    body: str
    cta: str
    trust: str
    questions: str
    email_label: str
    instagram_label: str


class Footer(Strict):
    tagline: str
    location: str
    cin_label: str
    cis_label: str
    rights: str


class NotFound(Strict):
    title: str
    body: str
    home: str


class PageContent(Strict):
    meta: Meta
    nav: Nav
    hero: HeroCopy
    facts: FactLabels
    about: Section
    trullo: Trullo
    features: list[Card] = Field(min_length=2, max_length=2)
    work: Section
    olive_oil: OliveOil
    dining: Dining
    gallery: Gallery
    location: Location
    faq: Faq
    book: Book
    footer: Footer
    not_found: NotFound
    alts: dict[str, str]
