# Villa El Carmen — Website

Static, multilingual site for Villa El Carmen, a private villa with a restored
trullo and pool among the olive groves of San Vito dei Normanni (Brindisi),
25 minutes from Ostuni and the Adriatic coast.

- **Live site**: <https://elcarmenpuglia.com/>
- **Languages**: English (`/`), Italian (`/it/`), German (`/de/`), French (`/fr/`), Spanish (`/es/`)
- **Hosting**: Vercel, serving the committed HTML as plain static files (no build on Vercel),
  plus one small function that reads the Airbnb calendar
- **Booking**: every call to action goes to the Airbnb listing, on the guest's local Airbnb domain.
  The booking section shows which nights are free; choosing dates opens the listing with them filled in

## How it works

The pages are generated from data, then committed:

```
src/site.json           facts shared by every language (address, CIN/CIS, distances, gallery)
src/content/<lang>.json all the copy for one language (titles, FAQ, alt text, ...)
src/templates/*.j2      Jinja2 templates
src/media.json          which photo becomes which web image
        │
        ▼  python -m sitebuild.build
index.html, it/, de/, fr/, es/, 404.html, sitemap.xml, robots.txt
```

See [docs/architecture.md](docs/architecture.md) for the details and
[docs/seo.md](docs/seo.md) for the search-engine choices.

## Setup

Python 3.11+ and Node 20+ (Node recompiles the CSS and runs the calendar tests).
`ffmpeg` is only needed to re-encode the hero video.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
npm --prefix tools/css ci
```

## Everyday tasks

| Task | Command |
|---|---|
| Change text in any language | edit `src/content/<lang>.json`, then `.venv/bin/python -m sitebuild.build` |
| Change a shared fact (distance, guests, CIN) | edit `src/site.json`, then rebuild |
| Change prices, seasons or minimum stays | first change the rule sets on Airbnb, then edit `pricing` in `src/site.json` the same way, rebuild and push (see below) |
| Show next year's prices | set `pricing.shown_year` in `src/site.json`, rebuild and push |
| Change the layout | edit `src/templates/`, rebuild, then recompile the CSS (below) |
| Recompile the CSS | `npm --prefix tools/css run css` |
| Add or replace a photo | put the original in `assets/images/`, map it in `src/media.json`, run `.venv/bin/python -m sitebuild.media --no-video`, then rebuild |
| Re-encode the hero video | `.venv/bin/python -m sitebuild.media` |
| Preview locally | `python3 -m http.server 8080`, open <http://localhost:8080/it/> (the calendar shows its error message: the function only runs on Vercel) |
| Run the checks | `.venv/bin/python -m pytest`, `.venv/bin/ruff check .` and `node --test tests/js/*.test.mjs` |

The build refuses to run when a language is missing alt text, a distance
label or an image, and the tests fail if the committed HTML is out of date
with `src/`, so always rebuild before committing.

## Deployment

Push to GitHub: Vercel deploys every branch as a preview and `main` to
production. `.vercelignore` limits the deployment to the generated pages and
`assets/` (without the full-size originals), and `vercel.json` sets trailing
slashes and cache headers.

After a push to `main` that changes a page, the **IndexNow** GitHub workflow
waits until Vercel serves the new HTML and submits the changed URLs to Bing
and the other IndexNow search engines. To submit every page, run the workflow
by hand from the Actions tab. To see the request without sending it:
`.venv/bin/python -m sitebuild.indexnow --all --dry-run`.

## Prices: one plan for the site and Airbnb

`pricing` in `src/site.json` is the only place the season plan is written:
seasons with price, minimum stay and the Airbnb rule set that charges them,
dated exceptions (for example Easter 2028), the days blocked every year and
`shown_year`, the year the pages show. The build turns it into the price
table, the price FAQ, `priceRange` in the structured data and `/prices.json`.

The weekly pricing check (separate repository) reads the live
`/prices.json` and compares it with Airbnb's calendar. When a price on
Airbnb no longer matches the site, or the season shown here has ended, it
says so in its weekly notification until the two agree again. So after
changing a rule set on Airbnb, change `src/site.json` too and push.

## Availability calendar

`api/availability.mjs` is a Vercel function that downloads the listing's
calendar export from Airbnb and returns only the booked nights as JSON
(`{"booked": [["2027-05-01", "2027-05-08"]], "until": "2028-05-04"}`).
Vercel's CDN caches the answer for an hour.

It needs one environment variable in the Vercel project, for Production and
Preview:

| Name | Value |
|---|---|
| `AIRBNB_ICAL_URI` | The link from Airbnb: Calendar → Availability → Connect calendars → Connect to another website. Keep the whole link, including `?t=…` |

The link is a secret: anyone with it can read the calendar, including links
to the reservations. It stays on the server and is never logged. Without it
the calendar shows a short message and the Airbnb button still works.

## Legal identifiers

The footer of every page shows the national identification code (CIN
IT074017C200100796) and the regional code (CIS BR07401791000058399), and
both are in the structured data. They live in `src/site.json`.
