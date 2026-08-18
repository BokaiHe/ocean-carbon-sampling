"""Map-first visual language for the OSSE notebook demo."""

from __future__ import annotations

from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cmocean
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm, TwoSlopeNorm

METHOD_LABELS = {
    "random": "Random",
    "historical_density": "Historical density",
    "spatial_coverage": "Spatial coverage",
}
YEAR_COLORS = {2005: "#1D4ED8", 2010: "#0F766E", 2014: "#7C3AED"}


def configure_theme() -> None:
    """Apply a compact notebook and vector-export-safe theme."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [
        "Arial",
        "Liberation Sans",
        "DejaVu Sans",
        "sans-serif",
    ]
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams.update(
        {
            "font.size": 7.0,
            "axes.titlesize": 8.0,
            "axes.labelsize": 7.0,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )


def _world_axis(fig: mpl.figure.Figure, spec: object) -> mpl.axes.Axes:
    ax = fig.add_subplot(
        spec,
        projection=ccrs.Robinson(central_longitude=180),
    )
    ax.set_global()
    ax.add_feature(cfeature.LAND, facecolor="#3F4347", edgecolor="none", zorder=3)
    ax.coastlines(color="#2B2F33", linewidth=0.35, zorder=4)
    return ax


def _grid(frame: pd.DataFrame, value: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    pivot = frame.pivot(index="latitude", columns="longitude", values=value)
    return (
        pivot.columns.to_numpy(dtype=float),
        pivot.index.to_numpy(dtype=float),
        pivot.to_numpy(dtype=float),
    )


def plot_sampling_atlas(
    sampling: pd.DataFrame,
    *,
    budget: int,
    seed: int,
) -> mpl.figure.Figure:
    """Show block-level sampling density for all three fixed-budget strategies."""
    configure_theme()
    order = ["random", "historical_density", "spatial_coverage"]
    maximum = float(sampling["observations"].max())
    norm = LogNorm(vmin=1.0, vmax=maximum)
    fig = plt.figure(figsize=(7.2, 2.35))
    grid = fig.add_gridspec(1, 3, left=0.02, right=0.98, bottom=0.22, top=0.82)
    image = None
    for index, strategy in enumerate(order):
        ax = _world_axis(fig, grid[0, index])
        subset = sampling.loc[sampling["strategy"] == strategy]
        lon, lat, values = _grid(subset, "observations")
        image = ax.pcolormesh(
            lon,
            lat,
            values,
            cmap=cmocean.cm.dense,
            norm=norm,
            shading="nearest",
            transform=ccrs.PlateCarree(),
            rasterized=True,
            zorder=2,
        )
        occupied = len(subset)
        ax.set_title(f"{METHOD_LABELS[strategy]}\n{occupied:,} occupied blocks")
        ax.text(
            0.02,
            0.04,
            chr(ord("a") + index),
            transform=ax.transAxes,
            fontweight="bold",
            fontsize=8,
            color="#111827",
            zorder=5,
        )
    if image is None:
        raise ValueError("sampling table is empty")
    color_ax = fig.add_axes([0.25, 0.10, 0.50, 0.035])
    colorbar = fig.colorbar(image, cax=color_ax, orientation="horizontal")
    colorbar.set_label("Selected month-grid observations per 5° × 10° block")
    fig.suptitle(
        f"Same budget, different observing geometry · n={budget:,}, seed={seed}",
        x=0.5,
        y=0.98,
        fontsize=9,
        fontweight="bold",
    )
    return fig


def plot_error_atlas(fields: pd.DataFrame) -> mpl.figure.Figure:
    """Contrast representative hidden-evaluation errors without downsampling."""
    configure_theme()
    random_col = "absolute_error_random"
    coverage_col = "absolute_error_spatial_coverage"
    difference_col = "absolute_error_difference_coverage_minus_random"
    finite_error = fields[[random_col, coverage_col]].to_numpy(dtype=float)
    error_limit = float(np.nanquantile(finite_error, 0.98))
    difference = fields[difference_col].to_numpy(dtype=float)
    difference_limit = float(np.nanquantile(np.abs(difference), 0.98))

    fig = plt.figure(figsize=(7.2, 4.8))
    grid = fig.add_gridspec(
        2,
        2,
        left=0.03,
        right=0.97,
        bottom=0.12,
        top=0.92,
        hspace=0.32,
        wspace=0.06,
    )
    hero = _world_axis(fig, grid[0, :])
    lon, lat, values = _grid(fields, difference_col)
    difference_image = hero.pcolormesh(
        lon,
        lat,
        values,
        cmap=cmocean.cm.balance,
        norm=TwoSlopeNorm(
            vmin=-difference_limit,
            vcenter=0.0,
            vmax=difference_limit,
        ),
        shading="nearest",
        transform=ccrs.PlateCarree(),
        rasterized=True,
        zorder=2,
    )
    hero.set_title(
        "Where coverage changes error · blue = coverage better, red = random better",
        pad=3,
    )
    hero.text(
        0.01,
        0.04,
        "a",
        transform=hero.transAxes,
        fontweight="bold",
        fontsize=8,
        zorder=5,
    )
    difference_bar = fig.colorbar(
        difference_image,
        ax=hero,
        orientation="horizontal",
        fraction=0.055,
        pad=0.04,
    )
    difference_bar.set_label("Coverage − random mean absolute error (µatm)")

    error_image = None
    for index, (column, title) in enumerate(
        [(random_col, "Random"), (coverage_col, "Spatial coverage")]
    ):
        ax = _world_axis(fig, grid[1, index])
        lon, lat, values = _grid(fields, column)
        error_image = ax.pcolormesh(
            lon,
            lat,
            values,
            cmap=cmocean.cm.amp,
            vmin=0.0,
            vmax=error_limit,
            shading="nearest",
            transform=ccrs.PlateCarree(),
            rasterized=True,
            zorder=2,
        )
        ax.set_title(f"{title} absolute error")
        ax.text(
            0.01,
            0.04,
            chr(ord("b") + index),
            transform=ax.transAxes,
            fontweight="bold",
            fontsize=8,
            zorder=5,
        )
    if error_image is None:
        raise ValueError("field table is empty")
    error_bar = fig.colorbar(
        error_image,
        ax=[axis for axis in fig.axes if hasattr(axis, "projection")][-2:],
        orientation="horizontal",
        fraction=0.055,
        pad=0.05,
    )
    error_bar.set_label("Mean absolute error on the hidden evaluation set (µatm)")
    fig.suptitle(
        "Representative spatial error pattern · 2005, budget 5,000, seed 0",
        fontsize=9,
        fontweight="bold",
    )
    return fig


def plot_tradeoff_summary(effects: pd.DataFrame) -> mpl.figure.Figure:
    """Show the three-year paired-seed tradeoff with bootstrap intervals."""
    configure_theme()
    metric_order = ["rmse", "p99_absolute_error", "median_absolute_error"]
    titles = ["RMSE", "Severe error (p99)", "Typical error (median)"]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.25), sharey=True)
    for panel, (ax, metric, title) in enumerate(zip(axes, metric_order, titles)):
        subset = effects.loc[effects["metric"] == metric].sort_values("year")
        for y_position, row in enumerate(subset.itertuples(index=False)):
            ax.errorbar(
                row.mean_difference,
                y_position,
                xerr=np.array(
                    [
                        [row.mean_difference - row.seed_bootstrap_low],
                        [row.seed_bootstrap_high - row.mean_difference],
                    ]
                ),
                fmt="o",
                color=YEAR_COLORS[int(row.year)],
                markersize=4.5,
                capsize=2,
                linewidth=1.1,
            )
            ax.annotate(
                str(int(row.year)),
                (row.seed_bootstrap_high, y_position),
                xytext=(3, 0),
                textcoords="offset points",
                va="center",
                fontsize=6.5,
                color=YEAR_COLORS[int(row.year)],
            )
        ax.axvline(0.0, color="#9CA3AF", linewidth=0.8, linestyle="--")
        ax.set_title(title)
        ax.set_xlabel("Coverage − random (µatm)")
        ax.set_yticks([])
        ax.grid(axis="x", color="#E5E7EB", linewidth=0.6)
        ax.text(
            0.02,
            0.96,
            chr(ord("a") + panel),
            transform=ax.transAxes,
            va="top",
            fontweight="bold",
            fontsize=8,
        )
    fig.text(
        0.06,
        0.02,
        "Negative = coverage better",
        color="#0F766E",
        fontsize=6.5,
    )
    fig.text(
        0.94,
        0.02,
        "Positive = random better",
        ha="right",
        color="#B45309",
        fontsize=6.5,
    )
    fig.suptitle(
        "The tradeoff repeats across years · mean paired effect and 95% seed-bootstrap interval",
        fontsize=9,
        fontweight="bold",
        y=1.03,
    )
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    return fig


def save_figure_bundle(fig: mpl.figure.Figure, output_stem: str | Path) -> None:
    """Export editable vectors plus high-resolution raster previews."""
    stem = Path(output_stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".png"), dpi=600, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".tiff"), dpi=600, bbox_inches="tight")
