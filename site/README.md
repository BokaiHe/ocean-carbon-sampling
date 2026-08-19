# Static interactive brief

This site contains no backend and performs no model fitting. It reads the frozen
`data/site-data.json` contract and swaps pre-rendered PNG maps.

Rebuild the data contract and maps from the repository root:

```bash
python scripts/build_static_site_assets.py
```

Preview locally:

```bash
python -m http.server 8000 --directory site
```

Then open `http://localhost:8000/`.
