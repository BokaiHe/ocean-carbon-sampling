# Notebooks

- Use `notebooks/work/` for disposable exploration; it is ignored by Git.
- Move only clean, rerunnable narrative notebooks into `notebooks/published/`.
- Reusable processing, modeling, metrics, and plotting logic belongs in `src/`, not in notebooks.

## Published notebooks

- `published/osse_results_walkthrough.ipynb` — rerunnable regional-to-global
  results narrative, including the ocean-mask audit (sections 6–7) and the
  existing-network augmentation pilot (section 8) behind the website's numbers.
  It reads tracked tables in `results/public/` and the saved runs in
  `experiments/network_augmentation_2005/`; it fits no models.
- `published/osse_visual_story_demo.ipynb` — map-first demo that inherits the
  original course project's visual language while using the redesigned OSSE,
  hidden-evaluation errors, and paired-seed statistics.
