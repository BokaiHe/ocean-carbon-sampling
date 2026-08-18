"""Preview or download the immutable CMIP6 files for the first OSSE pilot."""

from __future__ import annotations

import argparse
import os
import shutil
import urllib.request
from pathlib import Path

import yaml

from ocean_carbon_sampling.cmip6 import audit_local_file, load_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/osse_pilot.yaml")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="show the download plan")
    mode.add_argument("--download", action="store_true", help="download missing files")
    parser.add_argument("--skip-checksum", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    manifest = load_manifest(config["cmip6"]["manifest"])
    destination = Path(config["cmip6"]["raw_directory"])
    total = int(manifest.loc[manifest["required"], "size_bytes"].sum())

    print(f"Destination: {destination.resolve()}")
    print(f"Required download: {total / 1_000_000_000:.2f} GB")
    for row in manifest.itertuples(index=False):
        target = destination / row.filename
        print(f"\n{row.variable}: {row.size_bytes / 1_000_000:.1f} MB")
        print(f"  {row.url}")
        print(f"  -> {target}")

    if not args.download:
        print("\nDry run only. Re-run with --download to transfer the files.")
        return

    destination.mkdir(parents=True, exist_ok=True)
    free_bytes = shutil.disk_usage(destination).free
    if free_bytes < total * 1.1:
        raise OSError("Insufficient free disk space for the required CMIP6 files")

    for row in manifest.itertuples(index=False):
        target = destination / row.filename
        current = audit_local_file(
            target,
            expected_size=row.size_bytes,
            expected_sha256=row.sha256,
            verify_checksum=not args.skip_checksum,
        )
        if current["status"] == "ready":
            print(f"Already verified: {target.name}")
            continue
        _download_with_resume(row.url, target)
        final = audit_local_file(
            target,
            expected_size=row.size_bytes,
            expected_sha256=row.sha256,
            verify_checksum=not args.skip_checksum,
        )
        if final["status"] != "ready":
            raise OSError(f"Downloaded file failed integrity checks: {target}")
        print(f"Verified: {target.name}")


def _download_with_resume(url: str, target: Path) -> None:
    partial = target.with_suffix(target.suffix + ".part")
    offset = partial.stat().st_size if partial.exists() else 0
    request = urllib.request.Request(url)
    if offset:
        request.add_header("Range", f"bytes={offset}-")
    with urllib.request.urlopen(request) as response:
        append = offset > 0 and response.status == 206
        mode = "ab" if append else "wb"
        with partial.open(mode) as handle:
            shutil.copyfileobj(response, handle, length=8 * 1024 * 1024)
    os.replace(partial, target)


if __name__ == "__main__":
    main()
