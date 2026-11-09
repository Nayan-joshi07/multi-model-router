import asyncio
import os
from .base import Provider, Completion


class MockProvider(Provider):
    """Free, offline provider for learning. Set MOCK_FAIL=mock-fast to
    simulate an outage and watch the fallback chain kick in."""

    async def complete(self, model_id, prompt, max_tokens):
        if model_id in os.getenv("MOCK_FAIL", "").split(","):
            raise RuntimeError(f"simulated outage for {model_id}")
        await asyncio.sleep(0.05 if model_id == "mock-fast" else 0.2)
        text = f"[{model_id}] echo: {prompt[:200]}"
        return Completion(text, len(prompt) // 4, len(text) // 4)
