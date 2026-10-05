# Architecture

## Goals

- One page per language, each fully translated (not machine-switched in the
  browser), so search engines index five separate pages.
- Plain static files on Vercel: nothing to build or run in production.
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
| `index.html`, `it/` … `es/`, `404.html`, `sitemap.xml`, `robots.txt` | Generated pages | no (`sitebuild.build`) |
| `assets/css/site.css` | Compiled, minified CSS | no (`npm run css`) |
| `assets/img/`, `assets/video/`, `assets/icons/web/` | Generated web media | no (`sitebuild.media`) |
| `assets/images/`, `assets/videos/`, `assets/icons/*.png` | Originals, the source for the generated media | add only |

## The builder

- `sitebuild/models.py`: pydantic models for `site.json` and each language
  file. Length limits on titles (≤ 65 characters) and descriptions
  (70–160) keep search snippets from being cut. The CIN format is checked.
- `sitebuild/content.py`: loads the JSON and cross-checks it. Every
  language must have alt text for every image it shows, a label for every
  distance, and the same number of FAQ items.
- `sitebuild/seo.py`: URLs, hreflang alternates, structured data, sitemap
  and robots.txt.
- `sitebuild/build.py`: renders every page with `StrictUndefined`, so a
  missing string fails the build instead of printing an empty gap.
- `sitebuild/media.py`: resizes photos to WebP at 480/960/1600 px (never
  upscaling), applies the camera rotation and drops EXIF data (including
  GPS), crops the 1200×630 share image, makes square web icons, the logo and
  favicon, and re-encodes the hero video with ffmpeg (24 s, 1280 px, no
  audio, `+faststart`).

## Front end

- Tailwind 3, compiled and purged against the templates and `main.js`.
- `assets/js/main.js` (deferred, no dependencies): mobile menu, reveal on
  scroll, dining carousel, an accessible lightbox for the gallery, and
  pausing the hero video for reduced motion or data saver.
- Images use `srcset`/`sizes`, explicit width and height, and lazy loading
  below the fold. The hero video has a poster image.

## Tests

`python -m pytest` checks the media helpers, the SEO helpers, the content
rules and the generated pages: one `h1` per page, language attribute, self
canonical, reciprocal hreflang, Airbnb links on the right domain, CIN/CIS in
the footer, valid JSON-LD, every referenced asset present and deployed, and
that the committed HTML matches a fresh build.
