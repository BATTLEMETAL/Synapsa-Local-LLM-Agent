"""
Synapsa — Windows Compatibility Layer
Zunifikowany moduł kompatybilności.
Inspirowany przez: Audytor.py, Obserwator.py, FIX_LIBRARY.py, napraw_triton_crash.py
"""
import os
import sys
import warnings
import importlib.util


def setup_windows_compatibility():
    """Pancerny setup kompatybilności dla Windows + RTX - sprawdzony w Audytor.py i Obserwator.py."""
    warnings.filterwarnings("ignore")

    # Environment variables z Audytor.py i Obserwator.py
    os.environ["WBITS_USE_TRITON"] = "0"
    os.environ["UNSLOTH_USE_TRITON"] = "0"
    os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    os.environ.setdefault("TORCH_CUDA_ARCH_LIST", "8.6")  # RTX 3060

    # --- Triton Mock (Verified in Audytor.py) ---
    # Tworzy atrapę Tritona, która połyka wszystkie argumenty i nie powoduje błędów
    dummy_code = '''
class UniversalMock:
    def __init__(self, name="Mock"): self._name = name
    def __getattr__(self, item): return self
    def __call__(self, *args, **kwargs): return self
    def __iter__(self): return iter([])
    def __bool__(self): return False
    def __getitem__(self, key): return self
    def __int__(self): return 1
    def __float__(self): return 1.0
    __version__ = "3.0.0"

_mock = UniversalMock()
def cdiv(x, y): return (x + y - 1) // y
def next_power_of_2(n): return 1
def autotune(*args, **kwargs): return lambda fn: fn
def jit(*args, **kwargs): return lambda fn: fn
def heuristics(*args, **kwargs): return lambda fn: fn
Config = _mock
compile = _mock
language = _mock
compiler = _mock
runtime = _mock
def __getattr__(name): return _mock
'''
    try:
        dummy_name = os.path.join(os.path.dirname(__file__), "_triton_dummy.py")
        with open(dummy_name, "w", encoding="utf-8") as f:
            f.write(dummy_code)
        spec = importlib.util.spec_from_file_location("triton", dummy_name)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Only inject if triton is not already properly installed
            if "triton" not in sys.modules:
                module.__path__ = []
                module.__package__ = "triton"
                sys.modules["triton"] = module
                sys.modules["triton.language"] = module
                sys.modules["triton.compiler"] = module
                sys.modules["triton.runtime"] = module
                sys.modules["triton.testing"] = module
    except Exception:
        pass

    # --- Torch compile disable (from compat.py original) ---
    try:
        import torch
        torch.compile = lambda *args, **kwargs: (lambda x: x)
    except ImportError:
        pass


# Auto-setup on import
setup_windows_compatibility()
