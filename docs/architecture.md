# Architecture

## Goals

- One page per language, each fully translated (not machine-switched in the
  browser), so search engines index five separate pages.
- Plain static files on Vercel: nothing to build in production, and a single
  function (the availability calendar) to run.
- Facts written once. Guests, bedrooms, drive times, CIN/CIS and the gallery
  live in `src/site.json` and appear identically in every language.
- Fast on a phone over a holiday connection.

## Layout

| Path | What it is | Edited by hand? |
|---|---|---|
| `src/site.json` | Shared facts and settings (`SiteConfig`) | yes |
| `src/content/<lang>.json` | All copy for one language (`PageContent`) | yes |
| `src/templates/` | Jinja2 templates: `page.html.j2`, `404.html.j2` and partials | yes |
| `src/styles/site.css` | Tailwind input with the site's components | yes |
| `src/media.json` | Photo → slug mapping, image widths, video and icon settings | yes |
| `src/images.generated.json` | Sizes of the generated images | no (`sitebuild.media`) |
| `sitebuild/` | The Python builder | yes |
| `tests/` | pytest suite | yes |
| `tools/css/` | Tailwind CLI, pinned; kept out of the root so Vercel sees no `package.json` | yes |
| `api/availability.mjs` | Vercel function: booked nights from the Airbnb calendar | yes |
| `lib/` | Code the function imports: iCalendar parsing and the request handling | yes |
| `assets/js/` | Front-end scripts; `dates.mjs` is shared with the function | yes |
| `assets/fonts/` | Instrument Serif and Work Sans (latin, WOFF2) with their OFL licences | add only |
| `tests/js/` | `node --test` suite for the calendar and the function | yes |
| `index.html`, `it/` … `es/`, `404.html`, `sitemap.xml`, `robots.txt`, `prices.json` | Generated pages and the public price plan | no (`sitebuild.build`) |
| `assets/css/site.css` | Compiled, minified CSS | no (`npm run css`) |
| `assets/img/`, `assets/video/`, `assets/icons/web/` | Generated web media | no (`sitebuild.media`) |
| `assets/images/`, `assets/videos/`, `assets/icons/*.png` | Originals, the source for the generated media. `assets/images/drive/` holds the 1200 px copies from the owner's Google Drive folder "villa-el-carmen-photos" | add only |

## The builder

- `sitebuild/models.py`: pydantic models for `site.json` and each language
  file. Length limits on titles (≤ 65 characters) and descriptions
  (70–160) keep search snippets from being cut. The CIN format is checked.
- `sitebuild/content.py`: loads the JSON and cross-checks it. Every
  language must have alt text for every image it shows, a label for every
  distance, and the same number of FAQ items.
- `sitebuild/seo.py`: URLs, hreflang alternates, structured data, sitemap
  and robots.txt.
- `sitebuild/pricing.py`: turns the season plan into the table rows, the
  closure note, the price FAQ answer, the JSON-LD price range and
  `prices.json`. Exceptions split a season into extra table rows for their
  year only. Language files hold only templates with `{placeholders}`; the
  build refuses a template with a missing or unknown placeholder. The models
  refuse overlapping seasons or exceptions, an exception or a blocked day in
  the winter closure, and impossible dates.
- `sitebuild/indexnow.py`: maps a git diff to page URLs, waits until Vercel
  serves the committed HTML and submits the URLs to IndexNow. Run by
  `.github/workflows/indexnow.yml` after pushes to `main`.
- `sitebuild/build.py`: renders every page with `StrictUndefined`, so a
  missing string fails the build instead of printing an empty gap.
- `sitebuild/media.py`: resizes photos to WebP at 480/960/1600/2400 px (never
  upscaling; 2400 px keeps full-width photos sharp on large screens), applies the camera rotation and drops EXIF data (including
  GPS), crops the 1200×630 share image, makes square web icons, the logo and
  favicon, and re-encodes the hero video with ffmpeg (24 s, 1280 px, no
  audio, `+faststart`).

## Front end

- Design: terracotta and sage palette, Instrument Serif headings and Work Sans
  text, in full-width bands (chosen in the Lovable mock-up "Puglia Property
  Dreams"; only the look was taken from it, the copy and structure are this
  repository's). Colours and fonts are Tailwind tokens in
  `tools/css/tailwind.config.js`; buttons use the darker terracotta so white
  text keeps a 4.5:1 contrast.
- Fonts are self-hosted, so the guest's browser makes no request to Google.
- Tailwind 3, compiled and purged against the templates and the scripts.
- `assets/js/main.js` (deferred, no dependencies): mobile menu, reveal on
  scroll, an accessible lightbox (photos are buttons), and pausing the hero
  video for reduced motion or data saver.
- `assets/js/calendar.mjs` (ES module): the availability calendar. The rules
  (which nights can start or end a stay, the Airbnb link with
  `check_in`/`check_out`/`adults`) are pure functions in `calendar-core.mjs`.
  It opens on the first month with a free night and never offers dates past
  the horizon the function returns.
- Images use `srcset`/`sizes`, explicit width and height, and lazy loading
  below the fold. The hero video has a poster image.
- Caching: pages link `site.css`, `main.js` and `calendar.mjs` with
  `?v=<content hash>` (`VERSIONED_ASSETS` in `sitebuild/build.py`), and
  `vercel.json` makes browsers revalidate css/js on every visit. Without
  this, a browser that cached the old stylesheet showed the redesigned HTML
  unstyled for up to a day after it went live.

## Availability function

`GET /api/availability/` (Node, `export default { fetch }`):

1. reads `AIRBNB_ICAL_URI`; without it, answers 503 and does not call Airbnb;
2. downloads the export (8 s timeout), checks it is an iCalendar file;
3. keeps only `DTSTART`/`DTEND` of each event: summaries and descriptions,
   which hold reservation links and phone digits, are never read out;
4. clips to today (Europe/Rome) … +365 days, the 12 months Airbnb exports
   (beyond them the export is empty, not free), and merges overlapping stays;
5. answers `{booked, until, updated}` with
   `Cache-Control: public, s-maxage=3600, stale-while-revalidate=86400, stale-if-error=86400`.

Errors answer 502 with `no-store` and log the reason without the URL.
`vercel.json` adds trailing slashes, so the page calls `/api/availability/`.

## Tests

`node --test tests/js/*.test.mjs` checks the date helpers, the iCalendar
parsing, the function (with a fake Airbnb) and the calendar rules.

`python -m pytest` checks the media helpers, the SEO helpers, the content
rules and the generated pages: one `h1` per page, language attribute, self
canonical, reciprocal hreflang, Airbnb links on the right domain, CIN/CIS in
the footer, valid JSON-LD, every referenced asset present and deployed, and
that the committed HTML matches a fresh build.
