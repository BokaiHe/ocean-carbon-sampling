# Interactive research brief

React + Vite presentation of frozen results. The browser performs no model fitting.

## Reading order

Question → workflow → one sampling globe → paired MAE → evaluation variants →
supporting error map → sample-count trade-offs → optional methods and sources.

The results use a React-controlled four-chapter index with one large chart panel
at a time. All scientific panels and their source links remain in the HTML;
without the navigation enhancement they appear sequentially. Direct links and
keyboard navigation select the appropriate chapter. The research footer closes
with the next question, attribution and contact links. These are original
implementations informed by the Showcase 7 and Footer 10 visual patterns, not
redistributed licensed template source.

The globe shows simulated sampling only. The flat error map is the sole spatial
outcome view, explicitly labelled as a 2005 full-domain supporting analysis.
Signed-bias sensitivity remains available in the collapsed Methods audit
(`#estimand`); direct links open that audit automatically.

The real-observation globe, flat sampling maps, coverage-count chart, archived
signed-bias map and CTD photo are no longer displayed. Their source data, assets
and exporters remain in the repository. Observed SOCAT values are downloadable
under Sources but are not fetched by the page. No scientific scores were changed.

## Preview

From the repository root:

```bash
npm ci
npm run dev
```

For a production preview, run `npm run build` and then `npm run preview`; open the
local URL printed by Vite. The private licensed visual components are optional
for local builds; public clones use the supplied fallback.

## Frozen assets and publication

`python scripts/build_static_site_assets.py` rebuilds the original data contract
and archived PNG maps. It is not needed for presentation-only changes.

The configured `npm run publish:site` builds and publishes compiled output only.
It requires the owner's local licensed components and GitHub access; never commit
licensed source files or credentials.
