"""Build the compact HFF target catalogue from generated web derivatives."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_catalog(data_dir: Path, output: Path) -> Path:
    entries = []
    for path in sorted(data_dir.glob("*.json")):
        if path.name == output.name:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") != "lensaudit.web-dataset/1":
            continue
        entries.append(
            {
                "id": payload["id"],
                "title": payload["title"].split(" · ", 1)[0],
                "redshift": payload["provenance"]["clusterRedshift"],
                "release": payload["provenance"]["release"],
                "filename": path.name,
            }
        )
    if len(entries) != 6:
        raise ValueError(f"Expected all six HFF targets, found {len(entries)}.")
    preferred = [
        "abell2744-sharon-v4cor",
        "macs0416-sharon-v4cor",
        "macs0717-sharon-v4cor",
        "macs1149-sharon-v4cor",
        "abells1063-sharon-v4",
        "abell370-sharon-v4",
    ]
    entries.sort(key=lambda item: preferred.index(item["id"]))
    output.write_text(
        json.dumps({"schema": "lensaudit.hff-catalog/1", "targets": entries}, separators=(",", ":")),
        encoding="utf-8",
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("web/public/data"))
    parser.add_argument("--output", type=Path, default=Path("web/public/data/catalog.json"))
    args = parser.parse_args()
    print(build_catalog(args.data_dir, args.output))


if __name__ == "__main__":
    main()
