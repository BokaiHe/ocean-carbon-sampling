"""Build the prespecified ocean-domain masks (M1, M2); no model fitting."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
import yaml
from scipy import ndimage

EIGHT = np.ones((3, 3), dtype=bool)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/osse_ocean_mask.yaml"))
    parser.add_argument(
        "--map-output",
        type=Path,
        default=Path("results/public/osse_ocean_mask_excluded.png"),
    )
    return parser.parse_args()


def water_union(paths: list[Path]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Locations with complete-case truth and predictors in any month of any year."""
    union = None
    latitude = longitude = None
    for path in paths:
        with xr.open_dataset(path, engine="h5netcdf") as dataset:
            complete = (
                np.isfinite(dataset["spco2"])
                & np.isfinite(dataset["tos"])
                & np.isfinite(dataset["sos"])
            ).any("time").values
            if latitude is None:
                latitude = dataset["latitude"].values
                longitude = dataset["longitude"].values
            elif not (
                np.array_equal(latitude, dataset["latitude"].values)
                and np.array_equal(longitude, dataset["longitude"].values)
            ):
                raise ValueError("processed years use different grids")
        union = complete if union is None else union | complete
    return union, latitude, longitude


def periodic_label(mask: np.ndarray) -> np.ndarray:
    """8-connected labels with longitude wrapping across the dateline."""
    labels, _ = ndimage.label(np.concatenate([mask, mask[:, :1]], axis=1), EIGHT)
    for row in range(labels.shape[0]):
        left, right = labels[row, 0], labels[row, -1]
        if left and right and left != right:
            labels[labels == right] = left
    labels = labels[:, :-1]
    # 8-connectivity also joins diagonal neighbours across the dateline.
    for row in range(labels.shape[0]):
        for step in (-1, 1):
            other = row + step
            if not 0 <= other < labels.shape[0]:
                continue
            left, right = labels[row, 0], labels[other, -1]
            if left and right and left != right:
                labels[labels == right] = left
    return labels


def flood_fill(
    allowed: np.ndarray,
    latitude: np.ndarray,
    longitude: np.ndarray,
    *,
    seed: tuple[float, float],
    latitude_box: tuple[float, float],
    longitude_box: tuple[float, float],
) -> np.ndarray:
    lat_ok = (latitude >= latitude_box[0]) & (latitude <= latitude_box[1])
    lon_ok = (longitude >= longitude_box[0]) & (longitude <= longitude_box[1])
    region = allowed & lat_ok[:, None] & lon_ok[None, :]
    i = int(np.flatnonzero(np.isclose(latitude, seed[0]))[0])
    j = int(np.flatnonzero(np.isclose(longitude, seed[1]))[0])
    if not region[i, j]:
        raise ValueError(f"seed {seed} is not an allowed water location")
    labels, _ = ndimage.label(region, EIGHT)
    return labels == labels[i, j]


def land_overlap(latitude: np.ndarray, longitude: np.ndarray) -> np.ndarray:
    """Whether any of 10 x 10 sub-points in each 1-degree cell is NE 1:110m land."""
    import shapely
    from cartopy.io import shapereader
    from shapely.ops import unary_union

    path = shapereader.natural_earth(resolution="110m", category="physical", name="land")
    land = unary_union(list(shapereader.Reader(path).geometries()))
    shapely.prepare(land)
    offsets = (np.arange(10) + 0.5) / 10 - 0.5
    d_lat, d_lon = np.meshgrid(offsets, offsets, indexing="ij")
    grid_lat, grid_lon = np.meshgrid(latitude, longitude, indexing="ij")
    points_lat = grid_lat.ravel()[:, None] + d_lat.ravel()[None, :]
    points_lon = grid_lon.ravel()[:, None] + d_lon.ravel()[None, :]
    inside = shapely.contains_xy(land, points_lon.ravel(), points_lat.ravel())
    return inside.reshape(points_lat.shape).any(axis=1).reshape(grid_lat.shape)


def land_like(water: np.ndarray, on_land: np.ndarray, max_hole: int) -> np.ndarray:
    """Non-water locations treated as land; small open-water binning holes are not."""
    labels = periodic_label(~water)
    sizes = np.bincount(labels.ravel())
    large = sizes[labels] > max_hole
    return ~water & (on_land | large)


def coastal_locations(water: np.ndarray, land: np.ndarray) -> np.ndarray:
    """Water locations with any of eight neighbours that is land-like."""
    padded = np.pad(land, ((1, 1), (0, 0)), constant_values=False)
    padded = np.concatenate([padded[:, -1:], padded, padded[:, :1]], axis=1)
    touches = ndimage.binary_dilation(padded, EIGHT)[1:-1, 1:-1]
    return water & touches


def build(config: dict) -> pd.DataFrame:
    osse = yaml.safe_load(Path(config["source"]["osse_config"]).read_text(encoding="utf-8"))
    template = str(osse["processing"]["processed_file_template"])
    years = [int(year) for year in config["mask"]["grid_union_years"]]
    water, latitude, longitude = water_union(
        [Path(template.format(year=year)) for year in years]
    )

    labels = periodic_label(water)
    ids, counts = np.unique(labels[labels > 0], return_counts=True)
    main = ids[np.argmax(counts)]
    m1 = water & (labels == main)

    marginal = np.full(water.shape, "", dtype=object)
    for name, spec in config["mask"]["marginal_seas"].items():
        filled = flood_fill(
            m1,
            latitude,
            longitude,
            seed=tuple(spec["seed"]),
            latitude_box=tuple(spec["latitude"]),
            longitude_box=tuple(spec["longitude"]),
        )
        if (filled & (marginal != "")).any():
            raise ValueError(f"marginal sea {name} overlaps another definition")
        marginal[filled] = name
    land = land_like(
        water,
        land_overlap(latitude, longitude),
        int(config["mask"]["coastal_max_hole_locations"]),
    )
    coastal = coastal_locations(water, land) & m1
    m2 = m1 & (marginal == "") & ~coastal

    grid_lat, grid_lon = np.meshgrid(latitude, longitude, indexing="ij")
    keep = water
    reason = np.where(
        ~m1,
        "disconnected_water",
        np.where(
            marginal != "",
            "marginal_sea",
            np.where(coastal, "coastal", ""),
        ),
    )
    return pd.DataFrame(
        {
            "latitude": grid_lat[keep],
            "longitude": grid_lon[keep],
            "component_id": labels[keep].astype(int),
            "connected_ocean": (labels == main)[keep],
            "marginal_sea": marginal[keep].astype(str),
            "coastal": coastal[keep],
            "in_m1": m1[keep],
            "in_m2": m2[keep],
            "exclusion_reason": reason[keep],
        }
    )


def plot(cells: pd.DataFrame, output: Path) -> None:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    styles = {
        "coastal (M2 only)": (cells["in_m1"] & cells["coastal"], "#9aa5b1", 2),
        "marginal sea (M2 only)": (cells["marginal_sea"] != "", "#2a7fb8", 3),
        "disconnected water (M1 and M2)": (~cells["in_m1"], "#d1495b", 5),
    }
    fig = plt.figure(figsize=(12, 6.2))
    ax = fig.add_subplot(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.add_feature(cfeature.LAND.with_scale("110m"), facecolor="#f1efe9", zorder=0)
    ax.coastlines("110m", linewidth=0.4, color="#555")
    ax.axhline(60, color="#333", linewidth=0.8, linestyle="--")
    for label, (mask, color, size) in styles.items():
        sub = cells.loc[mask]
        ax.scatter(
            sub["longitude"], sub["latitude"], s=size, color=color,
            transform=ccrs.PlateCarree(), label=f"{label}: {len(sub):,}", linewidths=0,
        )
    ax.legend(loc="lower left", fontsize=9, markerscale=3, frameon=True)
    ax.set_title("Locations excluded by the ocean-domain masks (dashed: 60°N cap)")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    cells = build(config)
    output = Path(config["mask"]["cells_file"])
    output.parent.mkdir(parents=True, exist_ok=True)
    cells.to_csv(output, index=False, lineterminator="\n")
    plot(cells, args.map_output)

    cap = float(config["mask"]["latitude_max"])
    below = cells["latitude"] < cap
    summary = pd.DataFrame(
        {
            "all_latitudes": cells["exclusion_reason"].replace("", "kept_in_m2").value_counts(),
            f"below_{cap:g}N": cells.loc[below, "exclusion_reason"]
            .replace("", "kept_in_m2")
            .value_counts(),
        }
    ).fillna(0).astype(int)
    print(summary.to_string())
    print("\nmarginal seas below cap:")
    print(cells.loc[below & (cells["marginal_sea"] != ""), "marginal_sea"].value_counts().to_string())
    print(f"\nM1 locations below cap: {int((below & cells['in_m1']).sum())}")
    print(f"M2 locations below cap: {int((below & cells['in_m2']).sum())}")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"\n{output} sha256 {digest}")


if __name__ == "__main__":
    main()
