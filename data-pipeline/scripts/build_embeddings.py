"""
NASA FLAME — Build Dense Semantic Embeddings Index (Phase R2)
Generates and validates local dense vector embeddings for all scientific knowledge records.
"""

from pathlib import Path
import sys
import json
import time
import argparse

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rag.embeddings import LocalEmbeddingService


def main():
    parser = argparse.ArgumentParser(description="Build dense semantic embeddings index for NASA FLAME RAG")
    parser.add_argument("--force", action="store_true", help="Force re-generation of embeddings even if cached")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="SentenceTransformer model name")
    args = parser.parse_args()

    records_file = BASE_DIR / "processed_data" / "rag" / "scientific_knowledge_records.json"
    if not records_file.is_file():
        print(f"Error: Records file not found at {records_file}")
        sys.exit(1)

    print("=" * 65)
    print("NASA FLAME — Semantic Embeddings Generation Pipeline")
    print("=" * 65)

    with open(records_file, encoding="utf-8") as f:
        records = json.load(f)

    print(f"Loaded {len(records)} scientific knowledge records from disk.")
    service = LocalEmbeddingService(base_dir=BASE_DIR, model_name=args.model)

    start_time = time.perf_counter()
    result = service.build_index(records, force_rebuild=args.force)
    elapsed = time.perf_counter() - start_time

    status = result["status"]
    rec_count = result["record_count"]
    dim = result["embedding_dimension"]

    print(f"\nEmbedding Status: {status.upper()}")
    print(f"Total Records Indexed: {rec_count}")
    print(f"Embedding Dimensions: {dim}")
    print(f"Model: {args.model}")
    print(f"Execution Time: {elapsed:.2f} seconds")

    # Verify artifacts
    emb_file = BASE_DIR / "processed_data" / "rag" / "embeddings.npy"
    manifest_file = BASE_DIR / "processed_data" / "rag" / "embeddings_manifest.json"

    print(f"\nArtifact Verification:")
    print(f"  • Embeddings: {emb_file.name} ({emb_file.stat().st_size / 1024:.1f} KB)")
    print(f"  • Manifest:   {manifest_file.name} ({manifest_file.stat().st_size} bytes)")
    print("=" * 65)


if __name__ == "__main__":
    main()
