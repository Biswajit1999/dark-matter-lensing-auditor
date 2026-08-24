from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path(__file__).parents[1] / "web" / "public" / "data" / "abell2744-sharon-v4cor.json"


def test_bundled_hff_derivative_has_traceable_sources() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert payload["schema"] == "lensaudit.web-dataset/1"
    assert payload["width"] == payload["height"] == 128
    expected_cells = payload["width"] * payload["height"]
    assert len(payload["light"]) == expected_cells
    assert len(payload["kappa"]) == expected_cells
    assert len(payload["footprint"]) == expected_cells
    assets = {asset["role"]: asset for asset in payload["provenance"]["sourceAssets"]}
    assert assets["light"]["sha256"] == "91e356f724745d89a200d449132dc9c6fbc34a3746fb612cd8b291730e9086dd"
    assert assets["kappa"]["sha256"] == "9e79d81186fe8d7e77abc46eb06c83e8312c84f1dea1df3ae331520640796545"
    assert "v4cor" in payload["provenance"]["release"]
