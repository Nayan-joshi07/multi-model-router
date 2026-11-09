import httpx
from .base import Provider, Completion


class GeminiProvider(Provider):
    async def complete(self, model_id, prompt, max_tokens):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.post(
                url, headers={"x-goog-api-key": self.api_key},
                json={"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"maxOutputTokens": max_tokens}},
            )
            r.raise_for_status()
            d = r.json()
        text = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
        u = d.get("usageMetadata", {})
        return Completion(text, u.get("promptTokenCount", 0), u.get("candidatesTokenCount", 0))
