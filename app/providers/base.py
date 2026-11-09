from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Completion:
    text: str
    input_tokens: int
    output_tokens: int


class Provider(ABC):
    """One adapter per vendor. All return the same Completion shape,
    which is what lets the router swap models freely."""

    def __init__(self, api_key: str | None, timeout: float):
        self.api_key = api_key
        self.timeout = timeout

    @abstractmethod
    async def complete(self, model_id: str, prompt: str, max_tokens: int) -> Completion: ...
