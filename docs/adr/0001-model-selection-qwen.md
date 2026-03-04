# ADR 0001: Selection of Qwen 2.5 as the Local LLM Engine

**Date:** 2026-03-04
**Status:** Accepted

## Context
Synapsa is designed as an autonomous AI engineering ecosystem capable of understanding complex coding architectures, generating, and reviewing Polish and English text seamlessly. We evaluated several local Small Language Models (SLMs) in the 7B-8B parameter range to serve as the core engine. The two main candidates were:
1. Meta Llama 3 (8B)
2. Qwen 2.5 Coder (7B)

## Decision
We elected to use **Qwen 2.5 Coder (7B)** as the primary local LLM engine over Llama 3.

## Rationale
- **Coding Benchmarks:** Qwen 2.5 Coder consistently outperforms Llama 3 8B on coding-specific benchmarks (like HumanEval and MBPP). Since Synapsa's main goal is code generation and self-healing, coding capabilities are the top priority.
- **Multilingual Support (Polish):** Qwen models have demonstrated superior native handling of the Polish language compared to Llama 3 out-of-the-box, which is critical for the bilingual nature of Synapsa (processing Polish user intents into code).
- **Context Window:** Qwen 2.5 offers a significantly larger effective context window out-of-the-box (up to 128k tokens vs Llama 3's 8k default), allowing the ingestion of much larger code repositories and context files without resorting to aggressive chunking or external memory mechanisms.
- **Quantization Compatibility:** Qwen 2.5 integrates seamlessly with `bitsandbytes` for NF4 (4-bit Normal Float) quantization, reducing the memory footprint to fit within standard consumer GPUs (under 8GB VRAM) while maintaining high inference quality.

## Consequences
- **Positive:** Better zero-shot coding ability, native understanding of Polish context, ability to process whole files in a single prompt.
- **Negative/Trade-offs:** Llama 3 has a larger general community ecosystem (e.g., prompt templates, GGUF variants), which required us to build slightly more custom prompt handling for the ChatML format preferred by Qwen.
