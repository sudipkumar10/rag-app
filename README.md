# Production-Grade Reusable RAG Pipeline

A highly scalable, modular, and multi-tenant Retrieval-Augmented Generation (RAG) system. Designed to solve real-world business problems by providing accurate, context-aware answers from uploaded documents with strict source citations and zero hallucinations.

## 🏗️ Architecture

_(Add an architecture diagram here using Excalidraw or draw.io)_

- **Frontend:** Next.js, Tailwind CSS
- **Backend API:** FastAPI (Python), Uvicorn
- **Background Jobs:** Celery, Redis
- **Vector Database:** Qdrant (for semantic search)
- **Relational Database:** PostgreSQL (for metadata and state tracking)
- **Object Storage:** MinIO (S3-compatible)
- **Observability:** Langfuse (Tracing and Evaluations)
- **LLM Engine:** Groq (openai/gpt-oss-20b) / BGE-M3 Embeddings

## ✨ Key Features

- **Multi-Tenancy:** Strict data isolation using tenant IDs and dynamic Qdrant collections.
- **Smart Intent Routing:** Fast-path processing for greetings (saves API costs and reduces latency).
- **Advanced Ingestion:** Supports PDF, TXT, CSV, and Excel with streaming and token-aware recursive chunking.
- **Evaluation & Tracing:** Integrated with RAGAS (for offline eval) and Langfuse (for real-time tracing).
- **Containerized:** Fully Dockerized for single-command deployment.

## 🚀 Quick Start (Local Development)

### Prerequisites

- Docker & Docker Compose
- Groq API Key (Get it free at console.groq.com)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/rag-app.git
   cd rag-app
   ```
