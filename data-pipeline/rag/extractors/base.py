"""
Base extractor utilities for NASA FLAME RAG ingestion.
Provides deterministic record ID generation, searchable text formatting,
and scientific keyword extraction.
"""

import re
from typing import List, Optional, Any


def build_record_id(prefix: str, identifier: str) -> str:
    """Generate a clean, deterministic, alphanumeric record ID."""
    clean_id = re.sub(r"[^a-zA-Z0-9]+", "_", identifier).strip("_").lower()
    return f"flame_{prefix}_{clean_id}"


def sanitize_str(val: Optional[Any]) -> Optional[str]:
    """Sanitize and strip string values; return None if blank or null."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s and s.lower() not in ("none", "null", "nan", "") else None


def format_searchable_text(
    title: str,
    investigation: str,
    record_type: str,
    objective: str,
    description: str,
    conditions: str,
    measurements: str,
    provenance: str,
    validation_flags: Optional[str] = None,
    limitations: Optional[str] = None,
) -> str:
    """
    Format a dense, structured scientific text block.
    Optimized for lexical BM25 keyword matching and dense embedding semantic retrieval.
    """
    sections = [
        f"TITLE: {title}",
        f"INVESTIGATION: {investigation} | TYPE: {record_type}",
        f"SCIENTIFIC OBJECTIVE: {objective}",
        f"EXPERIMENTAL SUMMARY: {description}",
        f"CONDITIONS & MATERIALS: {conditions}",
        f"MEASUREMENTS & CHANNELS: {measurements}",
        f"DATA PROVENANCE: {provenance}",
    ]

    if validation_flags:
        sections.append(f"DATA VALIDATION & QUALITY FLAGS: {validation_flags}")

    if limitations:
        sections.append(f"SCIENTIFIC LIMITATIONS: {limitations}")

    return "\n".join(sections)


def extract_keywords_from_text(*texts: str) -> List[str]:
    """Extract distinct, lowercase scientific keywords from text snippets."""
    tokens = set()
    for text in texts:
        if not text:
            continue
        words = re.findall(r"\b[a-zA-Z0-9_°%/-]{2,}\b", text.lower())
        for w in words:
            if not w.isdigit():
                tokens.add(w)
    return sorted(list(tokens))
