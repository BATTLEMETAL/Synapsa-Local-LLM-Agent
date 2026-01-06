# Synapsa: Autonomous Local MLOps Ecosystem 🧠

**Synapsa** is a research and development project focused on creating a self-improving, offline coding assistant capable of running on consumer-grade hardware (NVIDIA RTX 3060). Unlike cloud-based solutions, Synapsa is designed to understand the specific context, architecture, and coding style of the user by reverse-engineering the local codebase.

## 🚀 Key Innovations

### 1. Consumer Hardware Optimization
Running a specialized 7B model locally usually requires enterprise GPUs. Synapsa utilizes advanced optimization techniques to run efficiently on 12GB VRAM:
*   **4-bit Quantization (QLoRA):** Drastically reduces memory footprint while maintaining reasoning capabilities.
*   **Custom Environment Patches:** Solved compatibility issues with `bitsandbytes` and `triton` libraries on Windows native environments (non-WSL), implementing custom mocks for Linux-specific system calls.

### 2. "Chain of Thought" Data Generation
To reduce hallucinations, the system doesn't just train on code. It uses a **Teacher-Student architecture**:
*   **The Harvest:** A scanner analyzes the codebase.
*   **The Reasoner:** An external API (Gemini/Groq) generates synthetic "thought processes" (`<thinking>...</thinking>` tags) explaining *why* the code was written that way.
*   **The Training:** The local model is fine-tuned on this reasoning data, learning to plan before coding.

### 3. The "Self-Correction" Loop
The ecosystem includes a validation module (`TestSkutecznosci.py`) that periodically examines the model on "Hardcore" coding questions (Concurrency, Security patterns) to measure progress and prevent catastrophic forgetting.

## 🛠️ Tech Stack & Architecture

*   **Core Model:** Qwen 2.5 7B (Fine-tuned).
*   **Training Framework:** Unsloth (optimized for speed) + Peft.
*   **Hardware:** NVIDIA RTX 3060 (12GB VRAM).
*   **Language:** Python 3.10+.
*   **Key Libraries:** PyTorch, Transformers, BitsAndBytes, HuggingFace Hub.

## 🚧 Project Status

*   **Phase:** Active R&D / Prototype.
*   **Current Focus:** Implementing an autonomous "Refactoring Agent" capable of modifying project structure without human supervision.

---
*Note: Due to the proprietary nature of the dataset and experimental optimization patches, the full source code is available upon request for technical interviews.*
