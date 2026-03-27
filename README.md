# Synapsa: Autonomous Local LLM Agent

**Synapsa** is a modular, offline-first AI agent system. No cloud. No privacy leaks.

## Key Achievement
* -40% RAM usage via custom bitsandbytes NF4 patches on Windows
* * Self-healing code loop (Ultimate Auditor) - agent tests and fixes its own output
* * ChromaDB RAG memory - remembers project context
* * Teacher-Student fine-tuning pipeline

* ## Tech Stack
* * Model: Qwen 2.5 7B NF4 quantized
* * Training: Unsloth + PEFT LoRA
* * Memory: ChromaDB vector database
* * Optimization: bitsandbytes, Triton
* * Runtime: Python 3.10, PyTorch, HuggingFace
 
  * ## Quick Start
  * git clone https://github.com/BATTLEMETAL/Synapsa-Local-LLM-Agent.git
  * cd Synapsa-Local-LLM-Agent
  * pip install -r requirements.txt
  * python main.py
 
  * ## Roadmap
  * * NF4 quantization + bitsandbytes patches (done)
    * * ChromaDB RAG integration (done)
      * * Self-healing Ultimate Auditor (done)
        * * REST API wrapper (planned)
          * * LangChain migration (planned)
            * 
