"""
NASA FLAME — Earth Applications Package (Phase EA1)
Export service, models, taxonomy, and initial evidence catalog.
"""

from earth_applications.models import (
    EarthApplicationEvidence,
    EarthApplicationCategoryModel,
    EarthApplicationListResponse,
    EarthApplicationDetailResponse,
)
from earth_applications.taxonomy import (
    EARTH_APPLICATION_CATEGORIES,
    EVIDENCE_CLASSIFICATION_RUBRIC,
    VALIDATION_STATUS_RUBRIC,
)
from earth_applications.catalog import INITIAL_EARTH_APPLICATION_CATALOG
from earth_applications.service import EarthApplicationsService

__all__ = [
    "EarthApplicationEvidence",
    "EarthApplicationCategoryModel",
    "EarthApplicationListResponse",
    "EarthApplicationDetailResponse",
    "EARTH_APPLICATION_CATEGORIES",
    "EVIDENCE_CLASSIFICATION_RUBRIC",
    "VALIDATION_STATUS_RUBRIC",
    "INITIAL_EARTH_APPLICATION_CATALOG",
    "EarthApplicationsService",
]
