# Interactive research brief

React + Vite presentation of frozen results. The browser performs no model fitting.

## Reading order

Combined question, shipboard photo and looping Polarstern route → observed SOCAT globe → workflow → experimental globe → paired MAE → evaluation variants →
supporting error map → sample-count trade-offs → optional methods and sources.

The results use a React-controlled four-chapter index with one large chart panel
at a time. All scientific panels and their source links remain in the HTML;
without the navigation enhancement they appear sequentially. Direct links and
keyboard navigation select the appropriate chapter. The research footer closes
with the next question, attribution and contact links. These are original
implementations informed by the Showcase 7 and Footer 10 visual patterns, not
redistributed licensed template source.

The observation globe shows real SOCAT grid values, with a year selector and twelve
visible month tiles above the globe. It does not invent ship routes. The experiment
globe offers sampling, local MAE and difference-from-random views. Its error layers
and the flat error map are explicitly labelled 2005 full-domain supporting analyses.
Signed-bias sensitivity remains available in the collapsed Methods audit
(`#estimand`); direct links open that audit automatically.

The flat sampling maps, coverage-count chart and archived signed-bias map
remain off the page. Their assets and exporters are retained. Both globes
load lazily and retain white land with black coastlines above the data symbols.
The PS103 illustration uses a fixed Southern Ocean view and a 32-second loop
through original navigation records. It has no dragging, timeline or navigation
controls. Offscreen/background animation pauses; reduced motion shows a still.
It is not a CO₂ sampling mask. The NOAA CTD photo
is contextual and is not from that voyage. No scientific scores were changed.

All page text, controls and SVG labels use Arial, with a sans-serif fallback.
The final typography stylesheet overrides legacy serif and italic rules; hierarchy
uses size and weight rather than switching font families.

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
