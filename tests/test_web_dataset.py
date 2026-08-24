from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_web_dataset.py"
SPEC = importlib.util.spec_from_file_location("build_web_dataset", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_area_aggregate_preserves_constant_surface() -> None:
    values = np.full((41, 57), 2.75)
    reduced = MODULE.area_aggregate(values, 16)
    assert reduced.shape == (16, 16)
    assert np.allclose(reduced, 2.75)


def test_area_aggregate_rejects_non_image() -> None:
    with pytest.raises(ValueError, match="2D"):
        MODULE.area_aggregate(np.ones((3, 4, 5)), 16)


def test_light_derivative_is_finite_and_nonnegative() -> None:
    values = np.linspace(-1, 8, 256).reshape(16, 16)
    transformed = MODULE.prepare_light_derivative(values)
    assert np.isfinite(transformed).all()
    assert transformed.min() >= 0
