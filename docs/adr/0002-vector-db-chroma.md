# ADR 0002: Selection of ChromaDB for Vector Memory

**Date:** 2026-03-04
**Status:** Accepted

## Context
Synapsa requires a Vector Database to facilitate Retrieval-Augmented Generation (RAG). This vector store acts as the "long-term memory" for the agent, storing code snippets, documentation, and architectural context. We evaluated ChromaDB and Qdrant.

## Decision
We elected to use **ChromaDB** as the primary vector storage solution over Qdrant.

## Rationale
- **Local-First Simplicity:** ChromaDB can run entirely in-memory or be persisted to the local file system using SQLite/Parquet under the hood (`chromadb.PersistentClient`). This perfectly aligns with Synapsa's goal of being a lightweight, easily deployable local ecosystem without requiring a separate database server or Docker container just for storage.
- **Python Integration:** The Python SDK for ChromaDB is extremely mature and lightweight, making it easy to embed directly into the FastAPI backend and agent logic without complex connection pooling.
- **Scale:** While Qdrant offers superior performance at massive scale (millions of vectors) and advanced filtering (Payloads), the scope of Synapsa (managing project-level context, typically thousands to tens of thousands of vectors) does not require this overhead.
- **Dependency Management:** Including ChromaDB as a Python dependency (`pip install chromadb`) is significantly lower friction for new users cloning the repository than requiring them to spin up a Qdrant Docker image.

## Consequences
- **Positive:** Zero-configuration local deployment, seamless Python integration, reduced system resource requirements.
- **Negative/Trade-offs:** Less efficient at enterprise scale, fewer advanced vector search features (like highly complex metadata filtering) compared to Qdrant. If the project scales to multi-tenant or massive codebases, a migration to Qdrant or Milvus may be necessary.
