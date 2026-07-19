import json
from pathlib import Path

import chromadb

CHROMA_DIR = Path(__file__).parent / "storage" / "chroma"
ORGANIZER_CORPUS_PATH = Path(__file__).parent.parent / "data" / "rules" / "organizer_rule_corpus.jsonl"


def get_chroma_client():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def build_corpus_documents() -> list[dict]:
    """Load the organizer's real rule corpus (Task 15) -- one ready-to-embed passage per
    line, including the numeric MTSP limits and the safety/decision-boundary rules -- and
    shape it for ingest_corpus()."""
    docs = []
    with open(ORGANIZER_CORPUS_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            docs.append(
                {
                    "id": entry["rule_id"],
                    "text": entry["text"],
                    "metadata": {
                        "authority": entry["authority"],
                        "effective_date": entry["effective_date"] or "",
                        "source_url": entry["source_url"],
                        "source_locator": entry["source_locator"],
                    },
                }
            )
    return docs


def ingest_corpus() -> int:
    """Re-ingest the corpus from scratch. Deletes and recreates the collection first --
    upsert() alone never removes ids that existed in a prior corpus version but aren't in
    the current one (e.g. this collection held 8 stale synthetic-passage ids from before
    Task 20 replaced them with organizer_rule_corpus.jsonl's 11 real entries; upsert never
    cleaned them out, so /ask kept serving retired passages). A full reset avoids that
    class of drift no matter how the corpus file changes in the future."""
    client = get_chroma_client()
    try:
        client.delete_collection("mtsp_rules")
    except Exception:
        pass
    collection = client.create_collection("mtsp_rules")
    docs = build_corpus_documents()
    collection.upsert(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[d["metadata"] for d in docs],
    )
    return len(docs)
