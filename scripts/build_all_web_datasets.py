"""Rebuild every reviewed HFF browser derivative and its target catalogue."""

from __future__ import annotations

import argparse
from pathlib import Path

from lensaudit.hff import HFF_DATASETS

from build_web_catalog import build_catalog
from build_web_dataset import build_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hff-root", type=Path, default=Path("data/hff"))
    parser.add_argument("--prepared", type=Path, default=Path("data/hff/prepared"))
    parser.add_argument("--web-data", type=Path, default=Path("web/public/data"))
    parser.add_argument("--size", type=int, default=128)
    args = parser.parse_args()

    for dataset in HFF_DATASETS.values():
        source = args.hff_root / dataset.key
        output = args.web_data / f"{dataset.key}.json"
        build_dataset(
            args.prepared / dataset.prepared_light_filename,
            source / dataset.asset("kappa").filename,
            args.prepared / dataset.footprint_filename,
            source / "provenance.json",
            output,
            size=args.size,
        )
        print(output)
    print(build_catalog(args.web_data, args.web_data / "catalog.json"))


if __name__ == "__main__":
    main()
