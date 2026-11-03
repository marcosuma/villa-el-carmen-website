# SEO decisions

## Keywords

The copy is built on what guests search for when planning Puglia (research
from October 2026): *villa with pool*, *trullo*, *near Ostuni*, *olive
grove*, *close to the sea*, *Brindisi airport*. The title of every language
puts the two property words first and the best-known nearby town after them:

| Language | Title |
|---|---|
| EN | Trullo Villa with Pool near Ostuni, Puglia \| Villa El Carmen |
| IT | Villa con trullo e piscina vicino a Ostuni \| Villa El Carmen |
| DE | Trullo-Villa mit Pool bei Ostuni, Apulien \| Villa El Carmen |
| FR | Villa avec trullo et piscine près d'Ostuni \| Villa El Carmen |
| ES | Villa con trullo y piscina cerca de Ostuni \| Villa El Carmen |

Every title ends with the full name, Villa El Carmen: in October 2026 the
name was the only query bringing clicks, and the site ranked 4.8 for it.
The Airbnb titles use the same words (without the pool), so the website and
the listing reinforce each other.

## Location and drive times

The villa is in the countryside of San Vito dei Normanni, not in the Valle
d'Itria, so the copy says "near Ostuni".

Drive times were measured on Google Maps from the villa itself (not from the
town centre) on 5 October 2026. By the owner's choice, the site shows them
20% shorter. They live once in `src/site.json`; the same figures are written
out in the beach and airport FAQ answers and in the meta descriptions, so a
change means editing those too.

| Destination | Google Maps | Shown |
|---|---|---|
| San Vito dei Normanni | 10 min | 8 min |
| Ostuni | 25 min | 20 min |
| Specchiolla beach | 25 min | 20 min |
| Torre Guaceto | 30 min | 24 min |
| Brindisi airport | 30 min | 24 min |
| Lecce | 55 min | 44 min |
| Alberobello | 60 min | 48 min |
| Polignano a Mare | 60 min | 48 min |
| Bari airport | 1 h 30 | 1 h 12 |

The Airbnb listing (summary and "Your place" section, all 5 languages) shows
the same shortened times since 6 October 2026.

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
- `LodgingBusiness.priceRange` from the cheapest and dearest season
  (`€420–€740` in 2027).
- `FAQPage` with the questions shown on that page, in its language, including
  the price question generated from the seasons.

There is deliberately no `aggregateRating`. Google ignores self-served
reviews on a business's own site and may treat them as spam, so the 5.0
Airbnb rating appears only as visible text.

## AI assistants and agents

ChatGPT, Gemini, Copilot, Perplexity and Claude answer travel questions from
search indexes and the pages they can quote. Decisions:

- **Facts in plain HTML, from one source.** Seasons, prices per night and
  minimum stays come from `pricing` in `src/site.json` and appear as a table, a
  closure note and an FAQ answer in every language, plus `priceRange` in the
  JSON-LD and the machine-readable `/prices.json`. Prices are what the Airbnb rule sets charge; the text says Airbnb
  adds its fees and shows the final price, without guessing other charges.
- **Be in more than Google.** Bing feeds Copilot and is one of ChatGPT
  search's sources; Claude's web search uses Brave. A November 2026 test
  search outside Google returned the Airbnb listing but not this site. The
  site pings IndexNow on every page change (`sitebuild/indexnow.py`,
  `.github/workflows/indexnow.yml`); add it to Bing Webmaster Tools too
  (import from Search Console) so Bing reads the sitemap and reports traffic.
- **Open to AI crawlers.** `robots.txt` allows every user agent, including
  OAI-SearchBot, and Vercel has no firewall rules blocking bots.
- **No llms.txt.** Google said in June 2026 that Search ignores it, and studies
  find AI crawlers rarely request it.

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
4. Keep the Google Business Profile consistent with the name, address and
   website shown here.
5. Check the IndexNow workflow run in the GitHub Actions tab.
6. When the season plan changes on Airbnb, update `pricing` in
   `src/site.json`. The weekly pricing check reads `/prices.json` and reports
   any difference until the site and Airbnb agree.
