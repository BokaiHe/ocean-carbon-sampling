# Interactive research brief

A bilingual (English / 中文) single page built with Vite. The React layer is only
the video hero and the findings-cover background; everything else is static HTML
plus two small scripts. The browser reads frozen JSON and fits no models.

## Reading order

Video hero → wave transition → introduction → background (SOCAT globe) →
method (OSSE steps, sampling-rule heatmaps, augmentation design, experiment globe)
→ three findings → robustness → conclusion → limits → sources.

## Files

| File | Role |
|---|---|
| `index.html` | Page structure and English text (`data-i18n` marks translatable nodes) |
| `i18n.js` | Chinese text and the EN/中文 switch; remembers the choice per browser |
| `ocean.css` | All page styles, colour tokens and the eight-step type scale |
| `story.js` | Charts (D3), scroll chrome, depth gauge and reveals |
| `globes.js` | SOCAT observation globe and 2005 experiment globe |
| `src/` | React hero (`Hero.jsx` public fallback, `useLang.jsx`) and Mosaic backdrop |
| `data/` | Frozen JSON exported from `results/public/` and the augmentation runs |

English is the source text in the HTML; every `data-i18n` key must have a Chinese
entry in `i18n.js` (checked by `tests/test_site.py`). Script-generated labels use
`OCS.tr(english, chinese)`.

## Data

| JSON | Exporter (no model fitting) |
|---|---|
| `chart-data.json` | `scripts/export_site_chart_data.py` |
| `augmentation.json` | `scripts/export_site_augmentation.py` |
| `globe-data.json`, `globe-land.json` | `scripts/export_site_globe_data.py` |
| `observed-co2.json` | `scripts/export_site_observations.py` (needs the local SOCAT CSV) |

The experiment globe shows the 2005 full-domain run from before the ocean mask
and says so on the page.

## Preview and publish

```bash
npm ci
npm run dev
```

`npm run build` then `npm run preview` gives a production preview. The licensed
components in `site/licensed/` are optional; public clones build the fallback.
`npm run publish:site` publishes compiled output only and never uploads
`site/licensed`. After editing hero text, run `npm run render:hero` to refresh
the prerendered header in `index.html`.
