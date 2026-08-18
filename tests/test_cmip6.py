from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
import pytest

from ocean_carbon_sampling.cmip6 import (
    audit_local_file,
    inspect_cmip6_dataset,
    load_manifest,
)


def test_load_manifest_validates_and_parses_required(tmp_path):
    payload = b"cmip6"
    manifest_path = tmp_path / "manifest.csv"
    pd.DataFrame(
        [
            {
                "variable": "spco2",
                "required": "true",
                "filename": "truth.nc",
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "url": "https://example.org/truth.nc",
                "purpose": "truth",
            }
        ]
    ).to_csv(manifest_path, index=False)

    manifest = load_manifest(manifest_path)

    assert bool(manifest.loc[0, "required"]) is True
    assert int(manifest.loc[0, "size_bytes"]) == len(payload)


def test_manifest_rejects_insecure_url(tmp_path):
    manifest_path = tmp_path / "manifest.csv"
    pd.DataFrame(
        [
            {
                "variable": "spco2",
                "required": True,
                "filename": "truth.nc",
                "size_bytes": 1,
                "sha256": "0" * 64,
                "url": "http://example.org/truth.nc",
                "purpose": "truth",
            }
        ]
    ).to_csv(manifest_path, index=False)

    with pytest.raises(ValueError, match="HTTPS"):
        load_manifest(manifest_path)


def test_audit_local_file_checks_size_and_checksum(tmp_path):
    source = tmp_path / "truth.nc"
    payload = b"known bytes"
    source.write_bytes(payload)

    result = audit_local_file(
        source,
        expected_size=len(payload),
        expected_sha256=hashlib.sha256(payload).hexdigest(),
    )

    assert result["status"] == "ready"


def test_audit_local_file_reports_missing(tmp_path):
    result = audit_local_file(
        tmp_path / "missing.nc",
        expected_size=100,
        expected_sha256="0" * 64,
    )

    assert result["status"] == "missing"


def test_inspect_cmip6_dataset_reads_curvilinear_coordinates(tmp_path):
    xr = pytest.importorskip("xarray")
    source = tmp_path / "truth.nc"
    dataset = xr.Dataset(
        data_vars={
            "spco2": (
                ("time", "y", "x"),
                np.ones((2, 2, 3)),
                {"units": "Pa"},
            )
        },
        coords={
            "time": pd.date_range("2005-01-01", periods=2, freq="MS"),
            "nav_lat": (("y", "x"), np.zeros((2, 3))),
            "nav_lon": (("y", "x"), np.zeros((2, 3))),
        },
    )
    dataset.to_netcdf(source, engine="h5netcdf")

    result = inspect_cmip6_dataset(source, "spco2")

    assert result["units"] == "Pa"
    assert result["latitude_name"] == "nav_lat"
    assert result["time_start"] == "2005-01"
