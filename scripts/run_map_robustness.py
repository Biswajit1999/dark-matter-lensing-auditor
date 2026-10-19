"""Run model-product diagnostics on previously downloaded Merten FITS maps."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from lensaudit.observational_weak_lensing import _load_maps
from lensaudit.map_robustness import (
    lensing_jacobian_diagnostics, mass_sheet_invariance_audit, resolution_sensitivity,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_directory", type=Path, help="Directory containing previously downloaded official Merten FITS products")
    parser.add_argument("--output", type=Path, default=Path("research/merten-map-robustness.json"))
    args = parser.parse_args()
    maps, _ = _load_maps(args.map_directory)
    values = (maps["kappa"], maps["gamma1"], maps["gamma2"])
    factors = tuple(f for f in (1, 2, 4, 8) if min(values[0].shape) // f >= 4)
    report = {
        "data_kind": "published observationally constrained model products; not source-shear data",
        "source": "Merten v1 SaWLens Abell 2744 products from previously downloaded local FITS",
        "jacobian": lensing_jacobian_diagnostics(*values),
        "mass_sheet_invariance": mass_sheet_invariance_audit(*values),
        "resolution_sensitivity": resolution_sensitivity(*values, factors=factors),
        "limitations": [
            "Internal map consistency is not independent mass inference.",
            "Magnification diverges near critical curves and requires masking.",
            "Coarsening excludes border pixels when map shape is not divisible by block factor.",
            "Mass-sheet transform leaves reduced shear invariant and does not break degeneracy.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
