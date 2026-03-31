from core.engine import SynapsaEngine
from config import settings

class BaseAgent:
    def __init__(self, engine: SynapsaEngine):
        self.engine = engine
        self.name = "Base"

    def run(self, task: str):
        raise NotImplementedError