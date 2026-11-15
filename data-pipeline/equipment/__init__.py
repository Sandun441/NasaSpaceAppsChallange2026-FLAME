"""
NASA FLAME — Fire-Safety Equipment Research Module
"""

from equipment.taxonomy import (
    FIRE_SAFETY_CATEGORIES,
    VERIFIED_INVESTIGATIONS_REGISTRY,
    QUICK_START_RESEARCH_TEMPLATES,
)
from equipment.analyzer import EquipmentResearchAnalyzer
from equipment.service import FireSafetyEquipmentService

__all__ = [
    "FIRE_SAFETY_CATEGORIES",
    "VERIFIED_INVESTIGATIONS_REGISTRY",
    "QUICK_START_RESEARCH_TEMPLATES",
    "EquipmentResearchAnalyzer",
    "FireSafetyEquipmentService",
]
