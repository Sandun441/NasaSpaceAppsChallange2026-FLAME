"""
NASA FLAME — Research Gap Detection Package (Phases RG1 & RG2)
Dataset Coverage Analysis & Scientific Research Gap Detection Engine
"""

from .coverage_service import DatasetCoverageService
from .gap_detection_service import (
    ResearchGapDetectionService,
    GAP_TYPE_COVERAGE,
    GAP_TYPE_SPARSE,
    GAP_TYPE_MEASUREMENT,
    GAP_TYPE_METADATA,
    GAP_TYPE_INGESTION,
    GAP_TYPE_COMPARISON,
    VALID_GAP_TYPES,
)

__all__ = [
    "DatasetCoverageService",
    "ResearchGapDetectionService",
    "GAP_TYPE_COVERAGE",
    "GAP_TYPE_SPARSE",
    "GAP_TYPE_MEASUREMENT",
    "GAP_TYPE_METADATA",
    "GAP_TYPE_INGESTION",
    "GAP_TYPE_COMPARISON",
    "VALID_GAP_TYPES",
]
