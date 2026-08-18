"""CMIP6 manifest and file-integrity utilities for the global OSSE."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

MANIFEST_COLUMNS = {
    "variable",
    "required",
    "filename",
    "size_bytes",
    "sha256",
    "url",
    "purpose",
}


def load_manifest(path: str | Path) -> pd.DataFrame:
    """Load and validate the tracked CMIP6 file manifest."""
    manifest = pd.read_csv(
        path,
        dtype={
            "variable": "string",
            "filename": "string",
            "sha256": "string",
            "url": "string",
            "purpose": "string",
        },
    )
    missing = MANIFEST_COLUMNS.difference(manifest.columns)
    if missing:
        raise ValueError(f"Manifest is missing columns: {sorted(missing)}")
    if manifest.empty:
        raise ValueError("Manifest must contain at least one file")
    if manifest["variable"].duplicated().any():
        raise ValueError("Manifest variables must be unique")
    if manifest["filename"].duplicated().any():
        raise ValueError("Manifest filenames must be unique")

    manifest = manifest.copy()
    manifest["required"] = manifest["required"].map(_parse_bool)
    manifest["size_bytes"] = pd.to_numeric(
        manifest["size_bytes"], errors="raise"
    ).astype("int64")
    if (manifest["size_bytes"] <= 0).any():
        raise ValueError("Manifest file sizes must be positive")
    if not manifest["sha256"].str.fullmatch(r"[0-9a-fA-F]{64}").all():
        raise ValueError("Every manifest SHA-256 must contain 64 hexadecimal digits")
    if not manifest["url"].str.startswith("https://").all():
        raise ValueError("Every manifest URL must use HTTPS")
    return manifest


def sha256_file(path: str | Path, chunk_bytes: int = 8 * 1024 * 1024) -> str:
    """Calculate a file SHA-256 without loading it into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_bytes), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_local_file(
    path: str | Path,
    *,
    expected_size: int,
    expected_sha256: str,
    verify_checksum: bool = True,
) -> dict[str, object]:
    """Check whether a local file matches its immutable ESGF metadata."""
    source = Path(path)
    if not source.exists():
        return {
            "exists": False,
            "size_matches": False,
            "checksum_matches": False,
            "status": "missing",
        }

    size_matches = source.stat().st_size == int(expected_size)
    checksum_matches = False
    if size_matches and verify_checksum:
        checksum_matches = sha256_file(source) == expected_sha256.lower()
    elif size_matches:
        checksum_matches = True

    return {
        "exists": True,
        "size_matches": size_matches,
        "checksum_matches": checksum_matches,
        "status": "ready" if size_matches and checksum_matches else "invalid",
    }


def inspect_cmip6_dataset(path: str | Path, variable: str) -> dict[str, object]:
    """Inspect variable, coordinates, units and time coverage with xarray."""
    try:
        import xarray as xr
    except ImportError as exc:
        raise RuntimeError('Install OSSE dependencies with: pip install -e ".[osse]"') from exc

    with xr.open_dataset(path, decode_times=True, engine="h5netcdf") as dataset:
        if variable not in dataset.data_vars:
            raise ValueError(f"Expected variable {variable!r} is absent from {path}")
        latitude = _first_present(dataset.variables, ("lat", "latitude", "nav_lat"))
        longitude = _first_present(dataset.variables, ("lon", "longitude", "nav_lon"))
        time_name = _first_present(dataset.variables, ("time", "time_counter"))
        if latitude is None or longitude is None or time_name is None:
            raise ValueError("Dataset must expose latitude, longitude and time coordinates")

        values = dataset[variable]
        time = dataset[time_name]
        first = time.values[0]
        last = time.values[-1]
        return {
            "variable_present": True,
            "dimensions": ",".join(f"{name}:{size}" for name, size in values.sizes.items()),
            "units": values.attrs.get("units", ""),
            "latitude_name": latitude,
            "longitude_name": longitude,
            "time_name": time_name,
            "time_count": int(time.size),
            "time_start": _format_time(first),
            "time_end": _format_time(last),
        }


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError(f"Cannot parse boolean manifest value: {value!r}")


def _first_present(variables: object, candidates: tuple[str, ...]) -> str | None:
    return next((name for name in candidates if name in variables), None)


def _format_time(value: object) -> str:
    year = getattr(value, "year", None)
    month = getattr(value, "month", None)
    if year is not None and month is not None:
        return f"{year:04d}-{month:02d}"
    return str(value)[:7]
