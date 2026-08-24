from __future__ import annotations

import json
from pathlib import Path
import re


DATA_DIR = Path(__file__).parents[1] / "web" / "public" / "data"


def test_bundled_hff_catalog_has_six_traceable_targets() -> None:
    catalog = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["schema"] == "lensaudit.hff-catalog/1"
    assert len(catalog["targets"]) == 6
    assert len({target["id"] for target in catalog["targets"]}) == 6

    for target in catalog["targets"]:
        payload = json.loads((DATA_DIR / target["filename"]).read_text(encoding="utf-8"))
        assert payload["schema"] == "lensaudit.web-dataset/1"
        assert payload["id"] == target["id"]
        assert payload["width"] == payload["height"] == 128
        expected_cells = payload["width"] * payload["height"]
        assert len(payload["light"]) == expected_cells
        assert len(payload["kappa"]) == expected_cells
        assert len(payload["footprint"]) == expected_cells
        assets = {asset["role"]: asset for asset in payload["provenance"]["sourceAssets"]}
        assert set(assets) == {"light", "kappa"}
        assert all(re.fullmatch(r"[a-f0-9]{64}", asset["sha256"]) for asset in assets.values())


def test_corrected_targets_do_not_bundle_v4orig() -> None:
    for path in DATA_DIR.glob("*-v4cor.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert "v4cor" in payload["provenance"]["release"]
        assert all("v4orig" not in asset["filename"] for asset in payload["provenance"]["sourceAssets"])
