# frontend, Fair Lending Lab dashboard

Static Next.js 14 + TypeScript + Tailwind + Recharts. Built with `output: "export"` so the entire app is a static HTML and JS bundle, uploaded to Cloudflare Pages, hitting the API at `NEXT_PUBLIC_API_BASE` from the client.

## Local development

```bash
npm ci
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8702 npm run dev
# http://127.0.0.1:3001
```

## Production build

```bash
NEXT_PUBLIC_API_BASE=https://fair-lending-api.scottcampbell.io npm run build
# output in ./out, upload to Cloudflare Pages
```

## Layout

- `src/app/page.tsx`: main page with five tabs (Overview, Hypotheses, Family correction, Methods, About)
- `src/components/`: KPI tile, panel, hypothesis card, charts (denial by race, denial by income band, posterior), pill, header
- `src/lib/api.ts`: thin fetch client over the FastAPI service
- `src/lib/format.ts`: p-value, effect-size, CI, percentage formatters

## Visual rules

- Near-black canvas, single accent (`#4f8bf5`).
- Inter for text, IBM Plex Mono for numbers, both self-hosted via `next/font`.
- Tabular numerals on body. KPI tiles always show value, unit, sub-line, optional sparkline.
- No em or en dashes anywhere in copy or code, commas and ASCII hyphens only.
