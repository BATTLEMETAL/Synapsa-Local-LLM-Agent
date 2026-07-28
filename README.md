# Synapsa — Autonomous Local LLM Agent System

> **Offline-first, multi-agent AI platform running on consumer GPU.**  
> No cloud API. No privacy leaks. No per-query costs.

---

## What It Does

Synapsa is a modular, autonomous AI system built on **Qwen 2.5 7B (NF4 quantized)** running locally on an **RTX 3060 (12GB VRAM)**. It coordinates multiple specialized agents that can read documents, generate and self-fix code, and build persistent vector memory — all without sending a single byte to an external server.

**Designed use case:** Automated document auditing for regulated industries (VAT invoice validation against Polish tax law — KSeF 2026, MPP threshold detection).

---

## Key Technical Achievements

| Achievement | Detail |
|---|---|
| **VRAM reduction** | 14.2 GB → 4.5 GB (**−68%**) via NF4 quantization + double quantization |
| **Windows Triton fix** | Custom `triton_dummy_*.py` patches routing matmul ops to native CUDA — solves the bitsandbytes crash on non-WSL Windows |
| **Self-healing loop** | Ultimate Auditor agent: LLM generates code → runs it → if it fails → LLM reads the traceback and self-corrects |
| **Persistent RAG memory** | ChromaDB vector store — agents remember document context across sessions |
| **Fine-tuning pipeline** | Teacher-Student setup: Gemini/Groq generates Chain-of-Thought data → trains local model via Unsloth + LoRA (r=16) |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│               Synapsa Core                  │
├──────────────────┬──────────────────────────┤
│   Orchestrator   │    ChromaDB Memory       │
│  (Qwen 2.5 NF4)  │   (Persistent RAG)       │
├──────────────────┼──────────────────────────┤
│ Ultimate Auditor │  Fine-tune Pipeline      │
│  (self-healing)  │  (Unsloth + LoRA r=16)   │
├──────────────────┼──────────────────────────┤
│   Document OCR   │   Rule-based Validator   │
│ (PyMuPDF + tess) │ (NIP, VAT, KSeF, MPP)   │
└──────────────────┴──────────────────────────┘
```

---

## Agent Roster

- **SecureAuditAgent** — validates financial documents against Polish VAT law (KSeF 2026, MPP ≥15K PLN, NIP format, date fields)
- **Ultimate Auditor** — self-healing code execution loop: generate → run → fail → read traceback → fix → repeat
- **Koder Agent** — generates Python extraction scripts for structured document parsing
- **Sensei/Teacher** — consolidates knowledge into ChromaDB vector memory
- **Obserwator** — pipeline monitoring and logging

---

## Stack

```
Model        │ Qwen 2.5 7B · NF4 + double quantization (bitsandbytes)
Inference    │ PyTorch · device_map="auto" · lazy loading
Fine-tuning  │ Unsloth · PEFT · LoRA r=16 · ChatML format
Vector Store │ ChromaDB (persistent, local) · sentence-transformers
OCR / Parse  │ PyMuPDF (fitz) · pytesseract · pdfplumber · openpyxl
API          │ FastAPI · Streamlit UI · Pydantic
DevOps       │ Docker · docker-compose · pytest (38 unit tests) · pre-commit
```

---

## Cloud Companion

For cloud deployment, see **[Synapsa Cloud API](https://github.com/BATTLEMETAL/synapsa-cloud-api)** — the same auditing logic exposed as a serverless REST API (FastAPI + Pinecone + Groq Llama 3.3 70B), deployed on Railway.app.

---

## Limitations & Honest Notes

- Requires NVIDIA GPU with ≥6GB VRAM (tested on RTX 3060 12GB)
- Windows-only Triton patches are custom workarounds, not upstream fixes
- This is a **portfolio/research project** — not production-hardened SaaS

---

*Built by [Michał Zalewski](https://github.com/BATTLEMETAL) — open to collaboration and feedback.*
