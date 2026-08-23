from __future__ import annotations

from io import BytesIO
import json

import pytest

import lensaudit.hff as hff


def test_curated_release_excludes_known_bad_scaling():
    dataset = hff.get_hff_dataset("abell2744-sharon-v4cor")
    assert dataset.release.startswith("v4cor")
    assert "not v4orig" in dataset.warning
    assert {asset.role for asset in dataset.assets} == {"light", "kappa"}
    assert all(asset.url.startswith("https://archive.stsci.edu/") for asset in dataset.assets)


def test_unknown_dataset_fails_closed():
    with pytest.raises(ValueError, match="Unknown HFF dataset"):
        hff.get_hff_dataset("unreviewed-map")


def test_download_writes_hash_receipt(monkeypatch, tmp_path):
    payload = b"SIMPLEabc"
    asset = hff.HFFAsset("kappa", "tiny.fits", "https://archive.stsci.edu/tiny.fits", len(payload), "fixture")
    dataset = hff.HFFDataset(
        key="test",
        cluster="test",
        cluster_redshift=0.1,
        lens_team="test",
        lens_method="test",
        release="test",
        source_redshift=None,
        archive_page="https://archive.stsci.edu/",
        model_readme="https://archive.stsci.edu/readme",
        warning="fixture",
        assets=(asset,),
    )
    monkeypatch.setitem(hff.HFF_DATASETS, "test", dataset)
    monkeypatch.setattr(hff, "urlopen", lambda *_args, **_kwargs: BytesIO(payload))

    receipt = hff.download_hff_dataset("test", tmp_path)
    manifest = json.loads(receipt.read_text(encoding="utf-8"))
    record = manifest["dataset"]["assets"][0]
    assert record["actual_bytes"] == len(payload)
    assert len(record["sha256"]) == 64
    assert (receipt.parent / "tiny.fits").read_bytes() == payload
