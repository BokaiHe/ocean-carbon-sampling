# Notebooks

- Use `notebooks/work/` for disposable exploration; it is ignored by Git.
- Move only clean, rerunnable narrative notebooks into `notebooks/published/`.
- Reusable processing, modeling, metrics, and plotting logic belongs in `src/`, not in notebooks.

## Published notebooks

- `published/osse_results_walkthrough.ipynb` — rerunnable regional-to-global
  results narrative. Its inline visualization is explicitly a content draft;
  all redraw inputs come from tracked CSV files in `results/public/`.
