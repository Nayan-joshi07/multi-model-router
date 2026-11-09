import httpx
from .base import Provider, Completion


class OpenAIProvider(Provider):
    async def complete(self, model_id, prompt, max_tokens):
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model_id, "max_tokens": max_tokens,
                      "messages": [{"role": "user", "content": prompt}]},
            )
            r.raise_for_status()
            d = r.json()
        u = d.get("usage", {})
        return Completion(d["choices"][0]["message"]["content"],
                          u.get("prompt_tokens", 0), u.get("completion_tokens", 0))
