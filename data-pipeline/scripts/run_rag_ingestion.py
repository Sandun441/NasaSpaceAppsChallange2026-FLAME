"""
Executable runner for NASA FLAME Phase R1 RAG ingestion.
Usage:
    python scripts/run_rag_ingestion.py
"""

from pathlib import Path
import sys

# Ensure data-pipeline root is in sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rag.pipeline import RagIngestionPipeline


def main():
    print("=" * 60)
    print("NASA FLAME — RAG Preparation Pipeline (Phase R1)")
    print(f"Base Directory: {BASE_DIR}")
    print("=" * 60)

    pipeline = RagIngestionPipeline(BASE_DIR)
    manifest = pipeline.run()

    print("\n✓ Ingestion Completed Successfully!")
    print(f"Total Knowledge Records: {manifest['total_knowledge_records']}")
    print("\nRecords by Type:")
    for rtype, count in manifest["records_by_type"].items():
        print(f"  • {rtype:<18}: {count}")

    print("\nRecords by Investigation:")
    for inv, count in manifest["records_by_investigation"].items():
        print(f"  • {inv:<45}: {count}")

    print(f"\nMissing Field Annotations Tracked: {manifest['total_missing_field_annotations']}")
    print("\nGenerated Artifacts:")
    for art in manifest["artifacts_generated"]:
        print(f"  -> {art}")
    print("=" * 60)


if __name__ == "__main__":
    main()
