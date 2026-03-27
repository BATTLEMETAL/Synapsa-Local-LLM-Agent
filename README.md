# Synapsa: Autonomous Local LLM Agent

**Synapsa** is a modular, offline-first AI agent system running on consumer hardware.
No cloud. No external API. No privacy leaks.

## Key Achievements

- -40% RAM usage via custom Triton/bitsandbytes NF4 patches on Windows (non-WSL)
- - Self-healing code loop (Ultimate Auditor) - agent tests and fixes its own output
  - - ChromaDB RAG memory - agent remembers project context between sessions
    - - Teacher-Student fine-tuning pipeline (Gemini/Groq generates CoT data for local model)
     
      - ## Architecture
     
      - ```
        +------------------------------------------+
        |              Synapsa Core                |
        +-------------------+----------------------+
        |    Orchestrator   |   ChromaDB Memory    |
        |    (Qwen NF4)    |   (Vector RAG)       |
        +-------------------+----------------------+
        |  Ultimate Auditor |  Fine-tune Pipeline  |
        |  (self-healing)   |  (Unsloth + PEFT)   |
        +-------------------+----------------------+
                 runs fully offline
            NVIDIA RTX 3060 - 12GB VRAM
        ```

        ## Tech Stack

        | Component | Technology |
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

        Requirements: Python 3.10+, NVIDIA GPU 8GB+ VRAM, CUDA 11.8+

        ## Roadmap

        - [x] NF4 quantization + Windows bitsandbytes patches
        - [x] ChromaDB RAG memory integration
   - [x]      Self-healing Ultimate Auditor module
   - [x]      Teacher-Student CoT fine-tune pipeline
        - [ ] REST API wrapper for enterprise integration
        - [ ] LangChain/LangGraph migration
        - [ ] 
