# Triton Windows Compatibility Layer

> **TL;DR:** BitsAndBytes crashes on Windows because Triton has no official Windows support.
> These modules fix that — Qwen 2.5 7B with NF4 quantization runs stably on RTX 3060 without any cloud dependency.

---

## The Problem

`bitsandbytes` (the 4-bit quantization library) relies on **Triton kernel operations** for
matrix multiplication during inference. Triton is officially Linux/CUDA-only — loading an
NF4-quantized 7B model on Windows causes an immediate crash:

```
AttributeError: module 'triton' has no attribute 'cdiv'
ModuleNotFoundError: No module named 'triton.language'
RuntimeError: Expected all tensors to be on the same device (matmul dispatch fails)
```

This is a known, **unresolved upstream issue** in bitsandbytes. There's no official fix.

---

## Root Cause Analysis

Debugging the bitsandbytes source (`bitsandbytes/autograd/_functions.py` and the Triton matmul
kernel loader) revealed the exact callsites that fail on Windows:

```python
# bitsandbytes tries to call these at module import time:
triton.autotune(configs=[...], key=[...])   # → AttributeError
triton.jit                                  # → AttributeError
triton.language.constexpr                   # → ModuleNotFoundError
triton.cdiv(x, y)                           # → AttributeError
```

The crash happens **before any user code runs**, making it impossible to catch with a try/except
at the application level.

---

## Solution: Per-Agent Mock Modules

Instead of patching bitsandbytes globally (fragile, breaks with updates), each agent
gets a **local Triton mock injected into `sys.modules` before model load**:

```python
# Injected at the top of each agent file, before any bitsandbytes import
import sys
sys.modules['triton'] = __import__('triton_dummy_windows', fromlist=[''])
sys.modules['triton.language'] = sys.modules['triton']
sys.modules['triton.ops'] = sys.modules['triton']
```

The `UniversalMock` class absorbs **any** attribute access, function call, subscript, or
iteration without raising exceptions, while redirecting actual compute to native PyTorch CUDA ops.

### Why per-agent instead of global?

- Agents load at different times (lazy loading) — a global patch can race with library imports
- Different agents use different quantization configs — isolation prevents cross-contamination
- Easier to remove once official Windows support lands in bitsandbytes

---

## Files

| File | Agent | Notes |
|------|-------|-------|
| `triton_dummy_windows.py` | Accounting auditor (production) | Core implementation — most complete |
| `triton_dummy_hybrid.py`  | Hybrid inference mode | Adds `cdiv` and `next_power_of_2` |
| `triton_dummy_koder.py`   | Code-generation agent | Extended mock for jit compilation paths |
| `triton_dummy_sensei.py`  | Knowledge consolidation (ChromaDB write path) | Minimal mock |
| `triton_dummy_night.py`   | Overnight fine-tuning runner | Required for Unsloth training loop |
| `triton_dummy_train.py`   | Interactive training | Mirrors night trainer config |
| `napraw_triton_crash.py`  | Diagnostic + auto-repair | Run this when the model crashes on first load |

---

## Measured Impact

| Configuration | VRAM at Load | VRAM at Inference | Status |
|--------------|-------------|-------------------|--------|
| FP16 (no patches) | ~14.2 GB | ~15.8 GB | ❌ Crashes on Windows |
| NF4 + bitsandbytes (no patches) | — | — | ❌ AttributeError: cdiv |
| **NF4 + these patches** | **~4.5 GB** | **~5.8 GB** | ✅ Stable on RTX 3060 |

**68% VRAM reduction** vs FP16 baseline, running entirely locally — no cloud, no API keys, GDPR-compliant.

---

## Hardware Tested

- GPU: NVIDIA RTX 3060 12 GB (consumer grade)
- OS: Windows 11 Pro (build 22631)
- CUDA: 12.1
- bitsandbytes: 0.43+
- PyTorch: 2.2.1+cu121

---

## Usage

```python
# At the top of your agent file, BEFORE any other imports
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # project root
sys.modules['triton']          = __import__('triton_patches.triton_dummy_windows', fromlist=[''])
sys.modules['triton.language'] = sys.modules['triton']
sys.modules['triton.ops']      = sys.modules['triton']

# Now bitsandbytes imports work normally
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import torch

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct", quantization_config=bnb_config)
```

---

## When Official Support Lands

Once bitsandbytes ships official Windows + Triton support, remove the `sys.modules` injection
lines from each agent file. The rest of the code is unaffected.

Track upstream: [TimDettmers/bitsandbytes#issues](https://github.com/TimDettmers/bitsandbytes/issues)
