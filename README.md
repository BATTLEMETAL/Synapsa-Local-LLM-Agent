# Synapsa: Autonomous Local LLM Agent

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python)](https://python.org)
[![Model](https://img.shields.io/badge/Model-Qwen%202.5%207B%20NF4-orange)](https://huggingface.co/Qwen)
[![Hardware](https://img.shields.io/badge/GPU-RTX%203060%2012GB-76B900?logo=nvidia)](.)
[![Status](https://img.shields.io/badge/Status-Active%20R%26D-blue)](.)

**Synapsa** to modularny, offline-first system agentowy dzialajacy na sprzecie konsumenckim.
Bez chmury. Bez API. Bez prywatnosci wysylanej na zewnatrz.

---

## Kluczowe osiagniecia

- -40% zuzycia RAM dzieki wlasnym patchom Triton/bitsandbytes NF4 na Windows (non-WSL)
- - Self-healing code loop ("Ultimate Auditor") - agent sam testuje i naprawia wlasny output
  - - ChromaDB RAG memory - agent "pamieta" kontekst projektow miedzy sesjami
    - - Teacher-Student fine-tuning - Gemini/Groq generuje syntetyczne dane CoT, model lokalny sie uczy
     
      - ---

      ## Architektura

      ```
      +-----------------------------------------+
      |           Synapsa Core                  |
      +-----------------+-----------------------+
      |   Orchestrator  |   ChromaDB Memory     |
      |   (Qwen NF4)   |   (Vector RAG)        |
      +-----------------+-----------------------+
      | Ultimate Auditor|   Fine-tune Pipeline  |
      | (self-healing)  |   (Unsloth + PEFT)    |
      +-----------------+-----------------------+
               | runs fully offline |
          NVIDIA RTX 3060 | 12GB VRAM
      ```

      ## Tech Stack

      | Komponent | Technologia |
      |---|---|
      | Model | Qwen 2.5 7B (fine-tuned, NF4 quantized) |
      | Training | Unsloth + PEFT (LoRA) |
      | Vector Memory | ChromaDB |
      | Optimization | bitsandbytes, Triton (custom Windows patches) |
      | Runtime | Python 3.10+, PyTorch, HuggingFace Transformers |

      ## Quick Start

      ```bash
      git clone https://github.com/BATTLEMETAL/Synapsa-Local-LLM-Agent.git
      cd Synapsa-Local-LLM-Agent
      python -m venv venv
      venv\Scripts\activate
      pip install -r requirements.txt
      python main.py
      ```

      > **Wymagania:** Python 3.10+, NVIDIA GPU 8GB+ VRAM, CUDA 11.8+
      >
      > ## Status
      >
      > - [x] NF4 quantization + Windows bitsandbytes patches
      > - [ ] - [x] ChromaDB RAG memory integration
      > - [ ] - [x] Self-healing "Ultimate Auditor" module
      > - [ ] - [x] Teacher-Student CoT fine-tune pipeline
      > - [ ] - [ ] REST API wrapper for enterprise integration
      > - [ ] - [ ] LangChain/LangGraph migration
      > - [ ] 
