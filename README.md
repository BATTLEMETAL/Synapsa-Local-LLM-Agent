# Synapsa — Autonomous Local LLM Agent System

[![CI](https://github.com/BATTLEMETAL/Synapsa-Local-LLM-Agent/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/BATTLEMETAL/Synapsa-Local-LLM-Agent/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Model](https://img.shields.io/badge/Model-Qwen%202.5%207B%20NF4-FF6F00?style=flat&logo=huggingface&logoColor=white)](https://huggingface.co/Qwen)
[![Hardware](https://img.shields.io/badge/GPU-RTX%203060%2012GB-76B900?style=flat&logo=nvidia&logoColor=white)](https://github.com/BATTLEMETAL/Synapsa-Local-LLM-Agent/tree/master/triton_patches)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20R%26D-blue?style=flat)](./)

**Synapsa** is a modular, **offline-first autonomous AI agent system** running entirely on consumer hardware — no cloud, no API keys, no data leaving your machine.

Built around **Qwen 2.5 7B** with custom NF4 quantization and a proprietary Triton compatibility layer that enables stable inference on Windows (where official Triton support does not exist).

> **In active production use:** Synapsa serves as the AI engine for [Shortsyt](https://github.com/BATTLEMETAL/Shortsyt) — an autonomous YouTube Shorts pipeline that has generated **15,130+ views** and published **75+ videos** since March 2026, with zero human intervention.

---

## ✨ Key Achievements

| Achievement | Detail |
|---|---|
| 🔧 **Custom Triton patches** | Solved `AttributeError: triton.cdiv` crash on Windows — no upstream fix exists |
| 💾 **−68% VRAM usage** | From ~14.2 GB (FP16) → ~4.5 GB (NF4 + patches) on RTX 3060 |
| 🔁 **Self-healing code loop** | Ultimate Auditor agent iteratively tests and repairs its own output |
| 🧠 **Modular RAG extension** | ChromaDB vector memory available via `pip install synapsa[rag]` — optional extension for persistent context |
| 🎓 **Teacher-Student fine-tuning** | Gemini/Groq generates synthetic CoT data; local model learns from it (LoRA) |
| 🏭 **Production REST API** | FastAPI wrapper with `/health`, `/audit/invoice`, `/info` endpoints |
| 🐳 **Docker-ready** | Full `Dockerfile` + `docker-compose.yml` for deployment |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Synapsa Core                         │
├──────────────────────┬──────────────────────────────────┤
│   Orchestrator       │   Knowledge Store                │
│   (Qwen 2.5 7B NF4) │   (JSON core / ChromaDB [rag])  │
├──────────────────────┼──────────────────────────────────┤
│   Ultimate Auditor   │   Teacher–Student Fine-tune      │
│   (self-healing)     │   (Unsloth + PEFT LoRA)         │
├──────────────────────┼──────────────────────────────────┤
│   FastAPI REST API   │   Streamlit UIs                  │
│   (enterprise layer) │   (accounting + construction)   │
└─────────────────────────────────────────────────────────┘
            │ Runs fully offline — no internet required │
                  NVIDIA RTX 3060 · 12 GB VRAM
```

### Cross-Project Integration (IPC Bridge)

Synapsa also serves as the **AI backend for [Shortsyt](https://github.com/BATTLEMETAL/Shortsyt)**. Shortsyt runs in its own lightweight venv and calls Synapsa via a cross-venv IPC bridge:

```python
# shortsyt/synapsa_bridge.py — cross-venv LLM call
def generate_viral_script_with_synapsa(context, topic):
    if not _check_vram_available(min_gb=4.5):  # nvidia-smi guard
        return use_fallback_script()
    os.environ["SYNAPSA_CONTEXT_PAYLOAD"] = "|".join(context)  # bypass Windows arg limit
    result = subprocess.run([SYNAPSA_PYTHON, "bridge.py"], timeout=300, capture_output=True)
    return json.loads(result.stdout.strip().split('\n')[-1])
```

This pattern demonstrates: VRAM-aware model loading, cross-process JSON protocol, 300s timeout guard, and graceful fallback to 30 curated scripts.

### Agent Roster

| Agent | File | Role |
|---|---|---|
| **Ultimate Auditor** | `AuditorUltimate.py` | Invoice parsing, JSON extraction, self-healing loop |
| **Auditor Hybrid** | `AuditorHybrid.py` | Multi-mode inference (local + cloud fallback) |
| **Sensei** | `Sensei.py` | Teacher-Student orchestrator — calls Gemini/Groq to generate synthetic CoT training data for local LoRA fine-tuning |
| **Instructor** | `Instructor.py` | Teacher agent — generates synthetic training data |
| **Expert Scanner** | `ExpertScanner.py` | Document scanning and structural analysis |
| **Observer** | `Observer.py` | System monitoring and performance tracking |
| **Koder** | `koder.py` | Code generation agent |

---

## 🔬 Triton Windows Compatibility Layer

> **This is the most technically unique part of this project.**

`bitsandbytes` (4-bit quantization library) relies on Triton kernel ops that only officially support Linux. Loading an NF4 model on Windows crashes immediately:

```
AttributeError: module 'triton' has no attribute 'cdiv'
ModuleNotFoundError: No module named 'triton.language'
```

The solution — a per-agent mock injection into `sys.modules` before model load — **reduces VRAM from 14.2 GB to 4.5 GB** and enables stable inference on Windows without any cloud dependency.

📂 See full technical writeup: [`triton_patches/README.md`](triton_patches/README.md)

---

## 🚀 Quick Start

```bash
git clone https://github.com/BATTLEMETAL/Synapsa-Local-LLM-Agent.git
cd Synapsa-Local-LLM-Agent

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

pip install -e ".[dev]"

# Run the REST API
uvicorn api:app --reload

# Or launch the Streamlit UI (accounting use-case)
streamlit run app_ksiegowosc.py
```

> **Requirements:** Python 3.10+, NVIDIA GPU with 8 GB+ VRAM, CUDA 11.8+

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Qwen 2.5 7B Instruct (NF4 quantized, fine-tuned) |
| **Quantization** | bitsandbytes 0.43+ (4-bit NF4) |
| **Windows compat** | Custom Triton mock layer (`triton_patches/`) |
| **Fine-tuning** | Unsloth + PEFT (LoRA) |
| **Vector Memory** | ChromaDB *(optional — `pip install synapsa[rag]`)* |
| **API** | FastAPI + Uvicorn |
| **UI** | Streamlit |
| **Containerization** | Docker + docker-compose |
| **Runtime** | Python 3.10+, PyTorch 2.2+, HuggingFace Transformers |
| **CI** | GitHub Actions (lint: Ruff + Black, tests: pytest) |

---

## 🧪 Running Tests

```bash
pytest tests/ -v --tb=short
```

**38 tests** across business logic norms, invoice parsing (including Polish VAT edge cases), and agent interface contracts — designed to run headlessly in CI (no GPU required).

---

## 📊 VRAM Benchmarks

| Configuration | VRAM Load | VRAM Inference | Status |
|---|---|---|---|
| FP16 baseline | ~14.2 GB | ~15.8 GB | ❌ OOM on RTX 3060 |
| NF4 + bitsandbytes (no patches) | — | — | ❌ Crashes on Windows |
| **NF4 + Triton patches** | **~4.5 GB** | **~5.8 GB** | ✅ Stable |

---

## 📁 Project Structure

```
Synapsa/
├── triton_patches/          # Custom Windows Triton compatibility layer ⭐
├── synapsa/                 # Core package (importable)
│   ├── engine.py             #   Singleton inference engine — lazy load, ChatML, NF4 ⭐
│   ├── hardware.py           #   Auto hardware scan + profile generation
│   └── agents/               #   Agent base classes
├── agents/                  # Domain-specific agents
│   ├── accountant_agent.py   #   Invoice auditing, Polish VAT rules, JSON knowledge store
│   └── construction_agent.py #   Construction cost estimation, offline knowledge base
├── tests/                   # pytest test suite (CI-ready, 38 tests)
├── api.py                   # FastAPI REST API
├── app_ksiegowosc.py        # Streamlit UI — accounting
├── app_budowlanka.py        # Streamlit UI — construction
├── AuditorUltimate.py       # Self-healing invoice auditor loop
├── Instructor.py            # Teacher agent (synthetic CoT data generation)
├── Observer.py              # System monitoring agent
├── ExpertScanner.py         # Document scanning and structural analysis
├── trener.py                # Interactive LoRA fine-tuning
├── trener_nocny.py          # Overnight fine-tuning runner
├── Dockerfile               # Container definition
└── docker-compose.yml       # Multi-service orchestration
```

---

## 📋 Roadmap

- [x] NF4 quantization + Windows bitsandbytes patches
- [x] ChromaDB RAG extension (optional `[rag]` install)
- [x] Self-healing "Ultimate Auditor" module
- [x] Teacher-Student CoT fine-tune pipeline
- [x] REST API wrapper (FastAPI)
- [x] CI/CD pipeline (GitHub Actions)
- [ ] LangChain/LangGraph migration
- [ ] Multi-agent orchestration via AutoGen
- [ ] Web UI dashboard for agent monitoring

---

## 🤝 Related Projects

- [Shortsyt](https://github.com/BATTLEMETAL/Shortsyt) — **Active consumer of Synapsa's LLM engine.** Autonomous YouTube Shorts factory: Synapsa generates scripts via IPC bridge, pipeline publishes daily. 15,130+ total views, 75+ videos.
- [SalesBot](https://github.com/BATTLEMETAL/SalesBot) — Automated Excel→PDF sales report pipeline with 12 pytest tests and GitHub Actions CI.

---

*Built as an R&D project for exploring local LLM deployment on consumer hardware. All inference runs fully offline — GDPR-compliant by architecture.*
