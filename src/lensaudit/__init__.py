"""Public API for the dark-matter lensing auditor."""

from .core import AuditResult, audit_mass_light, kaiser_squires, make_synthetic_cluster
from .io import read_fits, read_fits_bytes

__all__ = [
    "AuditResult",
    "audit_mass_light",
    "kaiser_squires",
    "make_synthetic_cluster",
    "read_fits",
    "read_fits_bytes",
]

__version__ = "0.1.0"
