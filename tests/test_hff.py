from __future__ import annotations

from io import BytesIO
import json

import pytest

import lensaudit.hff as hff


def test_curated_release_excludes_known_bad_scaling():
    assert len(hff.HFF_DATASETS) == 6
    corrected = [dataset for dataset in hff.HFF_DATASETS.values() if dataset.key.endswith("v4cor")]
    assert len(corrected) == 4
    assert all("not v4orig" in dataset.warning for dataset in corrected)
    assert all({asset.role for asset in dataset.assets} == {"light", "kappa"} for dataset in hff.HFF_DATASETS.values())
    assert all(
        asset.url.startswith("https://archive.stsci.edu/")
        for dataset in hff.HFF_DATASETS.values()
        for asset in dataset.assets
    )


def test_late_hff_fields_use_reviewed_v4_release():
    for key in ("abells1063-sharon-v4", "abell370-sharon-v4"):
        dataset = hff.get_hff_dataset(key)
        assert dataset.release == "v4"
        assert "no v4cor variant" in dataset.warning


def test_prepared_filenames_are_target_specific():
    dataset = hff.get_hff_dataset("macs0416-sharon-v4cor")
    assert dataset.prepared_light_filename == "macs0416-f814w-on-sharon-v4cor-grid.fits"
    assert dataset.footprint_filename == "macs0416-f814w-reprojection-footprint.fits"


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
