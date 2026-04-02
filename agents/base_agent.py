from abc import ABC, abstractmethod
from core.client import client


class BaseAgent(ABC):
    client = client

    @abstractmethod
    def run(self, *args, **kwargs):
        pass
