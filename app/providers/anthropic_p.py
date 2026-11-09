import httpx
from .base import Provider, Completion


class AnthropicProvider(Provider):
    async def complete(self, model_id, prompt, max_tokens):
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                json={"model": model_id, "max_tokens": max_tokens,
                      "messages": [{"role": "user", "content": prompt}]},
            )
            r.raise_for_status()
            d = r.json()
        text = "".join(b.get("text", "") for b in d["content"] if b["type"] == "text")
        u = d.get("usage", {})
        return Completion(text, u.get("input_tokens", 0), u.get("output_tokens", 0))
