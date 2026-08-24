"""Public API for the dark-matter lensing auditor."""

from .core import AuditResult, audit_mass_light, kaiser_squires, make_synthetic_cluster
from .io import read_fits, read_fits_bytes
from .hff import HFF_DATASETS, download_hff_dataset, get_hff_dataset, prepare_hff_pair

__all__ = [
    "AuditResult",
    "audit_mass_light",
    "kaiser_squires",
    "make_synthetic_cluster",
    "read_fits",
    "read_fits_bytes",
    "HFF_DATASETS",
    "download_hff_dataset",
    "get_hff_dataset",
    "prepare_hff_pair",
]

__version__ = "0.3.0"
