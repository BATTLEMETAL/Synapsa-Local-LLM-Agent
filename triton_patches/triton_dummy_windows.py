
class UniversalMock:
    def __init__(self, name="Mock"): self._name = name
    def __getattr__(self, item): return self
    def __call__(self, *args, **kwargs): return self # Połyka argumenty (fix dla num_warps)
    def __iter__(self): return iter([])
    def __bool__(self): return False
    def __getitem__(self, key): return self
    def __int__(self): return 1
    def __float__(self): return 1.0

_mock = UniversalMock()
def cdiv(x, y): return (x + y - 1) // y
def next_power_of_2(n): return 1
def autotune(*args, **kwargs): return lambda fn: fn
def jit(*args, **kwargs): return lambda fn: fn
def heuristics(*args, **kwargs): return lambda fn: fn
Config = _mock
compile = _mock
