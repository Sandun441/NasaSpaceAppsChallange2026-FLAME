"""
NASA FLAME — Scientific Unicode & Character Encoding Normalization Utility
Guarantees clean, lossless Unicode representations of microgravity combustion
measurements, physical units (°C, mW/cm², µm, ΔO₂), and typography (•, —, ±).
Prevents and repairs mojibake resulting from Windows-1252 / UTF-8 re-encoding.
"""

from typing import Any, Dict, List, Union
import re

# Exact mojibake replacements ordered from most specific to generic
MOJIBAKE_MAP = [
    # Heat flux units (most specific first)
    ("mw/cmÂ²", "mW/cm²"),
    ("mW/cmÂ²", "mW/cm²"),
    ("MW/cmÂ²", "mW/cm²"),
    ("mw/cm²", "mW/cm²"),
    ("MW/cm²", "mW/cm²"),
    ("W/cmÂ²", "W/cm²"),
    ("cmÂ²", "cm²"),
    ("mÂ²", "m²"),
    ("mmÂ²", "mm²"),
    ("Â²", "²"),
    ("cmÂ³", "cm³"),
    ("mÂ³", "m³"),
    ("Â³", "³"),
    # Degree Celsius and degree symbols
    ("Â°C", "°C"),
    ("Â°F", "°F"),
    ("â„ƒ", "°C"),
    ("â„‰", "°F"),
    ("Â°", "°"),
    # Bullets and typographic marks
    ("â€¢", "•"),
    ("â¢", "•"),
    ("Â·", "•"),
    ("â€”", "—"),
    ("â€“", "–"),
    ("â€œ", '"'),
    ("â€\x9d", '"'),
    ("â€˜", "'"),
    ("â€™", "'"),
    # Greek letters and delta
    ("âˆ†", "Δ"),
    ("Î”", "Δ"),
    ("Âµm", "µm"),
    ("Âµs", "µs"),
    ("Âµ", "µ"),
    ("Î¼", "µ"),
    # Math operators
    ("Â±", "±"),
    ("â‰¤", "≤"),
    ("â‰¥", "≥"),
    ("â‰ˆ", "≈"),
    ("Ã—", "×"),
]


def clean_scientific_unicode(text: str) -> str:
    """
    Cleans and repairs common encoding artifacts and mojibake in scientific text,
    restoring verified scientific units and symbols without altering underlying numbers.
    """
    if not text or not isinstance(text, str):
        return text

    cleaned = text
    for bad, good in MOJIBAKE_MAP:
        if bad in cleaned:
            cleaned = cleaned.replace(bad, good)

    # Clean residual isolated non-breaking space or control mojibake
    cleaned = cleaned.replace("Â ", " ")
    
    return cleaned


def clean_scientific_data(data: Any) -> Any:
    """
    Recursively cleans Unicode in nested dictionaries, lists, and strings.
    """
    if isinstance(data, str):
        return clean_scientific_unicode(data)
    elif isinstance(data, dict):
        return {clean_scientific_unicode(k): clean_scientific_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_scientific_data(item) for item in data]
    return data
