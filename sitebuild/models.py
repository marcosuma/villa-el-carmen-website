"""Typed shapes of the site configuration and the per-language copy."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


MONTH_DAY = r"^\d{2}-\d{2}$"


class Season(Strict):
    """Nights that repeat every year at the same price and minimum stay."""

    start: str = Field(pattern=MONTH_DAY, description="MM-DD, first night")
    end: str = Field(pattern=MONTH_DAY, description="MM-DD, last night")
    price: int = Field(gt=0, description="Euro per night for the whole villa")
    min_nights: int = Field(gt=0)
    rule_set: str = Field(min_length=1, description="Airbnb rule set that charges this")


class PriceException(Strict):
    """Nights of one specific year priced differently from their season (e.g. Easter)."""

    start: date = Field(description="First night")
    end: date = Field(description="Last night")
    price: int = Field(gt=0)
    min_nights: int = Field(gt=0)
    rule_set: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class Pricing(Strict):
    """The one place the season plan lives: the pages, prices.json and, through
    prices.json, the weekly pricing check all read it."""

    shown_year: int = Field(ge=2026, description="Year whose prices the pages show")
    base_price: int = Field(gt=0, description="Airbnb base price the rule sets adjust")
    seasons: list[Season] = Field(min_length=1)
    exceptions: list[PriceException] = Field(default_factory=list)
    closed_days: list[str] = Field(
        default_factory=list, description="MM-DD nights blocked every year inside a season"
    )

    def season_dates(self, year: int) -> list[tuple[date, date, Season]]:
        return [
            (
                date.fromisoformat(f"{year}-{season.start}"),
                date.fromisoformat(f"{year}-{season.end}"),
                season,
            )
            for season in self.seasons
        ]

    def season_on(self, night: date) -> Season | None:
        for start, end, season in self.season_dates(night.year):
            if start <= night <= end:
                return season
        return None

    def exception_on(self, night: date) -> PriceException | None:
        for exception in self.exceptions:
            if exception.start <= night <= exception.end:
                return exception
        return None

    @model_validator(mode="after")
    def seasons_in_order_without_overlap(self) -> "Pricing":
        # Two consecutive years, so a 29 February in a season is caught either way.
        for year in (self.shown_year, self.shown_year + 1):
            try:
                spans = self.season_dates(year)
            except ValueError as error:
                raise ValueError(f"invalid season date in {year}: {error}") from error
            for start, end, season in spans:
                if end < start:
                    raise ValueError(f"season {season.start}..{season.end} ends before it starts")
            neighbours = zip(spans, spans[1:], strict=False)
            for (_, previous_end, previous), (next_start, _, following) in neighbours:
                if next_start <= previous_end:
                    raise ValueError(
                        f"seasons {previous.start}..{previous.end} and "
                        f"{following.start}..{following.end} overlap or are out of order"
                    )
        return self

    @model_validator(mode="after")
    def exceptions_inside_seasons(self) -> "Pricing":
        ordered = sorted(self.exceptions, key=lambda exception: exception.start)
        for exception in ordered:
            label = f"exception {exception.start}..{exception.end}"
            if exception.end < exception.start:
                raise ValueError(f"{label} ends before it starts")
            if exception.start.year != exception.end.year:
                raise ValueError(f"{label} crosses into another year")
            for night in (exception.start, exception.end):
                if self.season_on(night) is None:
                    raise ValueError(f"{label} falls outside the seasons (the villa is closed)")
        for previous, following in zip(ordered, ordered[1:], strict=False):
            if following.start <= previous.end:
                raise ValueError(
                    f"exceptions {previous.start}..{previous.end} and "
                    f"{following.start}..{following.end} overlap"
                )
        return self

    @model_validator(mode="after")
    def closed_days_inside_seasons(self) -> "Pricing":
        for day in self.closed_days:
            try:
                night = date.fromisoformat(f"{self.shown_year}-{day}")
            except ValueError as error:
                raise ValueError(f"invalid closed day {day!r}: {error}") from error
            if self.season_on(night) is None:
                raise ValueError(f"closed day {day} is already in the winter closure")
        return self


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
    pricing: Pricing
    indexnow_key: str = Field(pattern=r"^[A-Za-z0-9-]{8,128}$")

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


class PricesCopy(Strict):
    """Labels for the seasons table; {placeholders} are filled from site.json."""

    title: str = Field(description="Contains {year}")
    dates_header: str
    price_header: str
    stay_header: str
    price_format: str = Field(description="Contains {price}")
    nights_format: str = Field(description="Contains {nights}")
    months: list[str] = Field(min_length=12, max_length=12)
    day_format: str = Field(description="Contains {day} and {month}")
    note: str = Field(description="Contains {guests}")
    closed_note: str = Field(description="Contains {closed_from} and {closed_to}")
    faq_question: str
    faq_answer: str = Field(
        description="Contains {year}, {min_price}, {max_price}, {min_nights}, {max_nights}"
    )


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
    prices: PricesCopy
    footer: Footer
    not_found: NotFound
    alts: dict[str, str]
