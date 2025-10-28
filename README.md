# Villa El Carmen — Website

Static marketing site for Villa El Carmen, a private vacation villa in Puglia,
Italy. The site showcases the property, amenities (3 bedrooms, 3 bathrooms,
private pool, Starlink WiFi, BBQ, air conditioning), gallery, dining
experiences, location in Valle d'Itria, and contact details.

- **Live site**: [`https://elcarmenpuglia.com/`](https://elcarmenpuglia.com/)
- **Stack**: Vanilla HTML + Tailwind (CDN), no build step
- **Entry point**: `index.html`
- **Assets**: images, icons, and a hero video in `assets/`

## Quick start (local)

Open a local web server from the project root and visit the printed URL.

```bash
cd /Users/marco.suma/Personal/villa-el-carmen-website
python3 -m http.server 8080
# open http://localhost:8080
```

No install/build required (Tailwind is loaded via CDN in `index.html`).

## Deployment

Any static host works (GitHub Pages, Netlify, Vercel, S3/CloudFront). Upload the
repository as-is; the site is a single HTML file with static assets.

## Content overview

- `index.html`: single-page layout with sections for About, Features, Dining
  (carousel), Gallery, Location, and Contact. Includes a hero background video,
  lightbox, and minimal JS for navigation, animations, and carousel.
- `assets/icons`: PNG icons for features.
- `assets/images`: Photos for the gallery and content sections.
- `assets/videos`: Hero video in `.mov` and `.mp4` formats.

The page copy aligns with the live content on
[`https://elcarmenpuglia.com/`](https://elcarmenpuglia.com/) and emphasizes an
authentic Apulian stay in a historic lamia with olive groves and on-site extra
virgin olive oil.

## References

- Live website content:
  [`https://elcarmenpuglia.com/`](https://elcarmenpuglia.com/)
