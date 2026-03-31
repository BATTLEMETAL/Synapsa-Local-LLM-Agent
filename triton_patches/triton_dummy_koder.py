
class UniversalMock:
    def __init__(self, name="Mock"): self._name = name
    def __getattr__(self, item): return self
    def __call__(self, *args, **kwargs): return self
    def __iter__(self): return iter([]) # Kluczowe dla pętli for x in triton...
    def __getitem__(self, key): return self
    def __bool__(self): return False
    def __int__(self): return 1
    def __float__(self): return 1.0

import sys
mock = UniversalMock()
# Rejestrujemy atrapę wszędzie gdzie się da
sys.modules["triton"] = mock
sys.modules["triton.language"] = mock
sys.modules["triton.compiler"] = mock
