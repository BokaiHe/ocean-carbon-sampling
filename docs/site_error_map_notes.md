# Supporting error-map contract and QA

## Figure contract

- Claim: the saved 2005 full-domain analysis permits a spatial comparison of
  historical-density and random absolute errors, not an optimal-sampling map.
- One quantitative spatial panel; comparison role, no mechanism or significance
  claim. The figure is supporting evidence, not the aligned-domain primary map.
- Python/matplotlib/Cartopy, continuing the existing map pipeline. Style-only
  inheritance: white land, black coastline, Arial. No sampling-map statistic or
  signed-bias priority transformation is reused.
- Web export: 12 × 6.6 inch layout, 300 dpi PNG plus editable-text SVG/PDF; CSV and
  JSON QA record. This is a website figure, not a journal submission.

## Field mapping and integrity

Source: `results/public/osse_visual_demo_fields.parquet`, with its metadata CSV
and original exporter `scripts/export_osse_visual_demo_data.py`.

`absolute_error_historical_density - absolute_error_random` becomes
`delta_mae_uatm`. Latitude/longitude locate 1-degree grid-cell centres. Each
source error is averaged over 20 paired seeds, then available held-out months
at that location; subtraction commutes with these means. This is not the
absolute value of a mean signed error, or an area-weighted global contribution.

All 40,624 source locations are retained in the exported CSV. Of these, 37,920
have paired errors; 2,704 have no saved held-out error and remain missing, not
zero. No downsampling, smoothing, interpolation, model fitting, or new
prediction is performed. Natural Earth land/coastlines are a cartographic
overlay, not a new analytical exclusion.

The linear diverging scale is centred on zero and saturates at ±30 µatm;
colourbar extension arrows mark the tails. Saturated values remain unchanged
in the CSV. Exact saturation counts and full numerical range are recorded in
`site/data/supporting-error-map.json`. Grey water means no mapped error, not
historical zero support. The 60°N reference line does not crop the analysis.

## Interpretation boundaries

- One year, original full-domain hidden-cell protocol, 5,000 samples per rule.
- No uncertainty interval, hypothesis test, or sign-consistency dots: the
  saved historical-density field does not contain seed-level sign counts.
- The map does not decompose the primary area-weighted <60°N result; cropping
  cannot reproduce the aligned training pool.
- No claim that adding an observation to a coloured cell would remove its error.

## QA

The build verifies unique coordinates, matching missingness, finite nonnegative
source errors, regular 1-degree coordinates, and source metadata. The automated
source preflight is followed by rendered PNG inspection and browser layout QA.
The PNG is the web preview; the SVG preserves labels as editable text. Source
tables and original experimental scores are unchanged.

Source preflight: 11 passes, no failures. Three publication-format warnings
are accepted for this web-specific deliverable: PNG rather than TIFF, 300 dpi
rather than the 600 dpi submission default, and a wider-than-journal layout.
The PNG render was inspected and SVG labels verified as editable text;
desktop and 390/320 px browser layouts
were checked for label clipping and horizontal overflow. Values outside the
scale: 115 below −30 and 2,169 above +30 µatm. The complete data range is
approximately −130.27 to +327.29 µatm; saturation is only a colour mapping.
