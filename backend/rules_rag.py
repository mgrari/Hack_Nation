from pathlib import Path

import chromadb

from rules_corpus import load_mtsp_limits

CHROMA_DIR = Path(__file__).parent / "storage" / "chroma"


def get_chroma_client():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def build_corpus_documents() -> list[dict]:
    corpus = load_mtsp_limits()
    docs = []
    for size, tiers in corpus["limits"].items():
        docs.append(
            {
                "id": f"mtsp-{size}",
                "text": (
                    f"For a household of {size} in {corpus['area_name']}, the MTSP 60% AMI income "
                    f"limit is ${tiers['60']:,} and the 50% AMI income limit is ${tiers['50']:,}. "
                    f"Source: HUD MTSP FY2026 tables, effective {corpus['effective_date']}."
                ),
                "metadata": {
                    "household_size": size,
                    "effective_date": corpus["effective_date"],
                    "source_url": corpus["source_url"],
                },
            }
        )
    return docs


def ingest_corpus() -> int:
    client = get_chroma_client()
    collection = client.get_or_create_collection("mtsp_rules")
    docs = build_corpus_documents()
    collection.upsert(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[d["metadata"] for d in docs],
    )
    return len(docs)
