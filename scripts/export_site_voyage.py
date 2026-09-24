"""Export a cited navigation record for context, not experimental observations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from datetime import datetime
from pathlib import Path


def export(source: Path, destination: Path) -> dict:
    raw = source.read_bytes()
    body = raw.decode("utf-8").split("*/", 1)[1].strip()
    points = []
    breaks = []
    previous = None
    for row in csv.DictReader(io.StringIO(body), delimiter="\t"):
        stamp = row["Date/Time"]
        time = datetime.fromisoformat(stamp)
        lat, lon = float(row["Latitude"]), float(row["Longitude"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Invalid navigation position")
        if previous is not None:
            seconds = (time - previous).total_seconds()
            if seconds <= 0:
                raise ValueError("Navigation record is not strictly chronological")
            if seconds > 1800:
                breaks.append(len(points))
        points.append([stamp, lon, lat])
        previous = time
    result = {
        "metadata": {
            "ship": "Polarstern",
            "cruise": "PS103",
            "citation": "Boebel, Olaf (2017): Station list and links to master tracks in different resolutions of POLARSTERN cruise PS103 (ANT-XXXII/2), Cape Town - Punta Arenas, 2016-12-16 - 2017-02-03. Alfred Wegener Institute, PANGAEA.",
            "doi": "https://doi.org/10.1594/PANGAEA.875075",
            "source_url": "https://doi.pangaea.de/10.1594/PANGAEA.875075?format=textfile",
            "license": "CC-BY-3.0",
            "license_url": "https://creativecommons.org/licenses/by/3.0/",
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "source_file": "PS103-track.tab",
            "columns": ["source_timestamp", "longitude", "latitude"],
            "transformation": "All recorded positions and source timestamps retained, without interpolation or coordinate rounding. Speed and course omitted. Lines are interrupted where adjacent records are more than 30 minutes apart.",
            "purpose": "Background navigation example only; not CO2 sample locations, not a SOCAT mask, not used to fit or score the OSSE.",
            "count": len(points),
            "start": points[0][0],
            "end": points[-1][0],
            "gap_threshold_seconds": 1800,
        },
        "break_before": breaks,
        "points": points,
    }
    destination.write_text(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site", type=Path, default=Path(__file__).resolve().parents[1] / "site"
    )
    args = parser.parse_args()
    output = export(
        args.site / "data/PS103-track.tab", args.site / "data/voyage-track.json"
    )
    print(
        f"Exported {output['metadata']['count']} recorded positions; {len(output['break_before'])} gaps."
    )
