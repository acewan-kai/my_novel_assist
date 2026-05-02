"""Vector memory — ChromaDB semantic retrieval."""

from __future__ import annotations

from typing import Any


class VectorMemory:
    def __init__(self, collection: str = "novel_assist"):
        self.collection_name = collection
        self._col = None

    def _init(self):
        if self._col is not None:
            return
        try:
            import chromadb
            self._col = chromadb.Client().get_or_create_collection(self.collection_name)
        except Exception:
            self._col = None

    def store(self, doc_id: str, text: str, metadata: dict[str, Any] | None = None):
        self._init()
        if self._col:
            self._col.add(ids=[doc_id], documents=[text], metadatas=[metadata or {}])

    def query(self, q: str, n: int = 3) -> list[dict[str, Any]]:
        self._init()
        if not self._col:
            return []
        results = self._col.query(query_texts=[q], n_results=n)
        docs = []
        if results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                docs.append({"content": doc, "metadata": (results.get("metadatas") or [{}])[0].get(i, {})})
        return docs
