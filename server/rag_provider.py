import glob
import os
from typing import List

import chromadb
import ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter


class OllamaEmbeddingFunction(chromadb.EmbeddingFunction):
    def __init__(self, model_name: str = "nomic-embed-text"):
        self.model_name = model_name

    def __call__(self, input: List[str]) -> List[List[float]]:
        return ollama.embed(model=self.model_name, input=input).embeddings


class RagProvider:
    def __init__(self, config: dict):
        self._embed_model = config.get("ragEmbedModel", "nomic-embed-text")
        self._chunk_size = config.get("ragChunkSize", 500)
        self._chunk_overlap = config.get("ragChunkOverlap", 50)
        self._top_k = config.get("ragTopK", 3)
        self._books_dir = config.get("ragBooksDir", "books")
        self._db_path = config.get("ragDbPath", "data/chroma_db")
        self._collection_name = config.get("ragCollectionName", "spanish_books")

        self._collection: chromadb.Collection | None = None

    def _ensure_ready(self):
        if self._collection is not None:
            return
        os.makedirs(self._db_path, exist_ok=True)
        client = chromadb.PersistentClient(path=self._db_path)
        self._embedding_fn = OllamaEmbeddingFunction(model_name=self._embed_model)
        self._collection = self._load_or_build_collection(client)

    def search(self, query: str) -> str:
        self._ensure_ready()
        results = self._collection.query(query_texts=[query], n_results=self._top_k)
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        parts = [
            f"[Source: {meta['source']}]\n{doc}"
            for doc, meta in zip(documents, metadatas)
        ]
        return "\n\n---\n\n".join(parts)

    def _load_or_build_collection(self, client: chromadb.PersistentClient) -> chromadb.Collection:
        existing = [c.name for c in client.list_collections()]
        if self._collection_name in existing:
            collection = client.get_collection(
                name=self._collection_name,
                embedding_function=self._embedding_fn,
            )
            expected = len(self._load_and_chunk_books())
            actual = collection.count()
            if actual == expected:
                print(f"[RAG] Loaded existing index ({actual} chunks).", flush=True)
                return collection
            print(f"[RAG] Index incomplete ({actual}/{expected} chunks), rebuilding...", flush=True)
            client.delete_collection(self._collection_name)

        collection = client.create_collection(
            name=self._collection_name,
            embedding_function=self._embedding_fn,
        )
        chunks = self._load_and_chunk_books()
        if chunks:
            batch_size = 100
            total = len(chunks)
            for i in range(0, total, batch_size):
                batch = chunks[i:i + batch_size]
                collection.add(
                    ids=[c["id"] for c in batch],
                    documents=[c["text"] for c in batch],
                    metadatas=[c["metadata"] for c in batch],
                )
                print(f"[RAG] Indexed {min(i + batch_size, total)}/{total} chunks...", flush=True)
        return collection

    def _load_and_chunk_books(self) -> list[dict]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            length_function=len,
        )
        chunks = []
        for file_path in glob.glob(os.path.join(self._books_dir, "*.md")):
            filename = os.path.basename(file_path)
            if filename == "sources.md":
                continue
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            for i, chunk in enumerate(splitter.split_text(content)):
                chunks.append({
                    "id": f"{filename}_chunk_{i}",
                    "text": chunk,
                    "metadata": {"source": filename, "chunk": i},
                })
        return chunks
