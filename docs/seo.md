# SEO decisions

## Keywords

The copy is built on what guests search for when planning Puglia (research
from October 2026): *villa with pool*, *trullo*, *near Ostuni*, *olive
grove*, *close to the sea*, *Brindisi airport*. The title of every language
puts the two property words first and the best-known nearby town after them:

| Language | Title |
|---|---|
| EN | Villa with Trullo & Pool near Ostuni, Puglia \| El Carmen |
| IT | Villa con trullo e piscina vicino a Ostuni \| Villa El Carmen |
| DE | Villa mit Trullo und Pool bei Ostuni, Apulien \| El Carmen |
| FR | Villa avec trullo et piscine près d'Ostuni \| Villa El Carmen |
| ES | Villa con trullo y piscina cerca de Ostuni \| Villa El Carmen |

The Airbnb titles use the same words (without the pool), so the website and
the listing reinforce each other.

## Honest location

The villa is in the countryside of San Vito dei Normanni, not in the Valle
d'Itria, so the copy says "near Ostuni" and gives real drive times, measured
on Google Maps from the villa itself (not from the town centre). They live
once in `src/site.json` and are rounded to 5 minutes.

## Languages

- One URL per language: `/` (English, also the `x-default`), `/it/`,
  `/de/`, `/fr/`, `/es/`.
- Every page lists all five plus `x-default` as `hreflang` alternates, the
  same set on every page, and a canonical pointing to itself.
- `sitemap.xml` repeats the alternates with `xhtml:link`.
- The language switcher is plain links, so crawlers can follow it.
- Booking buttons go to the Airbnb domain of the page's language
  (airbnb.it, airbnb.de, ...).

## Structured data

Each page has one JSON-LD graph with:

- `WebSite`
- `LodgingBusiness`: address, coordinates, map link, check-in/out times,
  rooms, occupancy, amenities, `petsAllowed: false`, and the CIN and CIS as
  `PropertyValue` identifiers. The Airbnb listing and Instagram are listed
  under `sameAs`.
- `FAQPage` with the questions shown on that page, in its language.

There is deliberately no `aggregateRating`. Google ignores self-served
reviews on a business's own site and may treat them as spam, so the 5.0
Airbnb rating appears only as visible text.

## Technical

- `robots.txt` allows everything and points to the sitemap. `404.html` is
  `noindex`.
- `vercel.json` adds trailing slashes and long cache lifetimes for images and
  video.
- Lighthouse (mobile, Italian page, local server): Performance 97,
  Accessibility 100, Best Practices 96, SEO 100. The remaining points were
  Google Fonts being blocked in the test environment and missing compression
  and caching on the local test server, which Vercel provides.

## After each production deploy

1. Open `/robots.txt` and `/sitemap.xml` on the live domain and check that
   they load. An earlier version of the site removed them because of a
   Cloudflare block, so make sure no proxy or bot protection is in front of
   Vercel.
2. In Google Search Console (domain property), submit
   `https://elcarmenpuglia.com/sitemap.xml` and inspect `/` and `/it/`.
3. Check the structured data with Google's Rich Results Test.
4. Keep the Google Business Profile, if any, consistent with the name,
   address and website shown here.
