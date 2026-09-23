"""Render the supporting MAE difference map from saved errors; no model fits."""

from __future__ import annotations

import json
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 12,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
)

LIMIT = 30.0


def build_error_data(results_dir: Path) -> tuple[pd.DataFrame, dict]:
    source = pd.read_parquet(results_dir / "osse_visual_demo_fields.parquet")
    metadata = pd.read_csv(results_dir / "osse_visual_demo_metadata.csv").iloc[0]
    if (int(metadata.year), int(metadata.n_error_map_seeds), int(metadata.budget)) != (
        2005,
        20,
        5000,
    ):
        raise ValueError("Map contract requires 2005, 20 seeds and 5,000 samples")
    coordinates = ["latitude", "longitude"]
    errors = ["absolute_error_random", "absolute_error_historical_density"]
    if source.duplicated(coordinates).any():
        raise ValueError("Duplicate source coordinates")
    if not source[errors[0]].isna().equals(source[errors[1]].isna()):
        raise ValueError("Strategy error availability differs")
    for column in coordinates:
        values = source[column].to_numpy()
        if not np.isfinite(values).all() or not np.allclose(values % 1, 0.5):
            raise ValueError("Expected finite 1-degree cell centres")
    valid = source[errors[0]].notna()
    values = source.loc[valid, errors].to_numpy()
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Absolute errors must be finite and nonnegative")
    frame = source[coordinates].copy()
    frame["delta_mae_uatm"] = source[errors[1]] - source[errors[0]]
    delta = frame.loc[valid, "delta_mae_uatm"]
    audit = {
        "source": "results/public/osse_visual_demo_fields.parquet",
        "year": int(metadata.year),
        "seeds": int(metadata.n_error_map_seeds),
        "sample_count": int(metadata.budget),
        "scope": "Supporting: original full-domain hidden-cell evaluation",
        "definition": "Mean absolute error historical-density minus random, microatmospheres (uatm)",
        "aggregation": "20 paired seed means, then available held-out months per location; no area factor",
        "source_locations": len(frame),
        "finite_locations": int(valid.sum()),
        "missing_locations": int((~valid).sum()),
        "colour_limit_uatm": LIMIT,
        "below_colour_scale": int((delta < -LIMIT).sum()),
        "above_colour_scale": int((delta > LIMIT).sum()),
        "minimum_uatm": float(delta.min()),
        "maximum_uatm": float(delta.max()),
        "no_new_fits_or_predictions": True,
    }
    return frame, audit


def render_map(frame: pd.DataFrame, output_dir: Path) -> None:
    grid = frame.pivot(index="latitude", columns="longitude", values="delta_mae_uatm")
    grid = grid.reindex(
        index=np.arange(-89.5, 90, 1), columns=np.arange(-179.5, 180, 1)
    )
    cmap = LinearSegmentedColormap.from_list(
        "error_difference", ["#356e9c", "#f7f8f6", "#a65c45"]
    )
    cmap.set_bad("#cfd9df")
    fig, ax = plt.subplots(
        figsize=(12, 6.6), subplot_kw={"projection": ccrs.PlateCarree()}
    )
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#cfd9df")
    image = ax.imshow(
        grid.to_numpy(),
        origin="lower",
        extent=[-180, 180, -90, 90],
        interpolation="none",
        cmap=cmap,
        norm=Normalize(-LIMIT, LIMIT),
        transform=ccrs.PlateCarree(),
        zorder=1,
    )
    ax.add_feature(cfeature.LAND.with_scale("110m"), facecolor="white", zorder=3)
    ax.coastlines(resolution="110m", color="#1c2d38", linewidth=0.85, zorder=4)
    ax.plot(
        [-180, 180],
        [60, 60],
        color="#243b49",
        linestyle=(0, (5, 4)),
        linewidth=0.85,
        transform=ccrs.PlateCarree(),
        zorder=5,
    )
    ax.set_global()
    ax.set_xticks([-180, -120, -60, 0, 60, 120, 180], crs=ccrs.PlateCarree())
    ax.set_yticks([-60, -30, 0, 30, 60, 90], crs=ccrs.PlateCarree())
    ax.tick_params(labelsize=11, colors="#465b68")
    ax.spines["geo"].set_visible(False)
    ax.set_title(
        "Supporting analysis · 2005 · original full-domain hidden cells",
        fontsize=13,
        color="#243b49",
        pad=14,
    )
    bar = fig.colorbar(
        image,
        ax=ax,
        orientation="horizontal",
        pad=0.09,
        fraction=0.05,
        aspect=35,
        extend="both",
        ticks=[-30, -15, 0, 15, 30],
    )
    bar.set_label("Historical-density − random mean absolute error (µatm)", fontsize=12)
    bar.ax.set_xticklabels(["−30", "−15", "0", "+15", "+30"])
    bar.ax.tick_params(labelsize=11)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        output_dir / "supporting_mae_difference_2005.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    fig.savefig(
        output_dir / "supporting_mae_difference_2005.svg",
        bbox_inches="tight",
        facecolor="white",
    )
    fig.savefig(
        output_dir / "supporting_mae_difference_2005.pdf",
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


if __name__ == "__main__":
    frame, audit = build_error_data(Path("results/public"))
    output = Path("site/data")
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / "supporting-error-map.csv", index=False)
    (output / "supporting-error-map.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    render_map(frame, Path("site/assets/maps"))
    print(json.dumps(audit, indent=2))
