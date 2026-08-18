"""Audit downloaded CMIP6 OSSE inputs against the tracked ESGF manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

from ocean_carbon_sampling.cmip6 import (
    audit_local_file,
    inspect_cmip6_dataset,
    load_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/osse_pilot.yaml")
    parser.add_argument("--skip-checksum", action="store_true")
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--output", default="results/osse_work/input_audit.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    manifest = load_manifest(config["cmip6"]["manifest"])
    source_dir = Path(config["cmip6"]["raw_directory"])
    rows: list[dict[str, object]] = []

    for entry in manifest.itertuples(index=False):
        path = source_dir / entry.filename
        result = audit_local_file(
            path,
            expected_size=entry.size_bytes,
            expected_sha256=entry.sha256,
            verify_checksum=not args.skip_checksum,
        )
        row: dict[str, object] = {"variable": entry.variable, "path": str(path)}
        row.update(result)
        if result["status"] == "ready":
            row.update(inspect_cmip6_dataset(path, entry.variable))
        rows.append(row)

    audit = pd.DataFrame(rows)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(output, index=False)
    print(audit.to_string(index=False))

    required = manifest["required"].to_numpy(dtype=bool)
    if not (audit.loc[required, "status"] == "ready").all() and not args.allow_missing:
        raise SystemExit("Required OSSE inputs are missing or invalid")


if __name__ == "__main__":
    main()
