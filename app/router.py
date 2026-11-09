"""The core idea: pick a model per request, then fall back on failure.

Strategies:
  rules    - heuristics on the prompt (code? long? simple?)
  cheapest - lowest cost model that fits the context window
  quality  - highest quality model available
  explicit - caller names the model
"""
import re
import time
from dataclasses import dataclass

from .config import CATALOG, ModelSpec, settings
from .providers import REGISTRY, Completion

BY_NAME = {m.name: m for m in CATALOG}
CODE_HINTS = re.compile(r"```|\bdef |\bclass |\bfunction\b|\bbug\b|\berror\b|stack trace", re.I)
REASONING_HINTS = re.compile(r"\b(why|explain|analy[sz]e|compare|plan|prove|step by step)\b", re.I)


def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def available() -> list[ModelSpec]:
    return [m for m in CATALOG if settings.has_key(m.provider)]


def choose(prompt: str, strategy: str, model: str | None = None) -> tuple[ModelSpec, str]:
    """Return (model, reason). Pure function: easy to unit test."""
    pool = [m for m in available() if m.max_context >= est_tokens(prompt)]
    if not pool:
        raise ValueError("no model available for this prompt")

    if strategy == "explicit":
        if model not in BY_NAME:
            raise ValueError(f"unknown model {model!r}")
        return BY_NAME[model], "caller requested"

    if strategy == "cheapest":
        return min(pool, key=lambda m: m.cost_per_1k), "lowest cost"

    if strategy == "quality":
        return max(pool, key=lambda m: m.quality), "highest quality"

    # rules (default)
    tokens = est_tokens(prompt)
    if tokens > 50_000:
        m = max(pool, key=lambda m: m.max_context)
        return m, f"long prompt ({tokens} tok) -> biggest context"
    if CODE_HINTS.search(prompt) or REASONING_HINTS.search(prompt):
        return max(pool, key=lambda m: m.quality), "code/reasoning -> high quality"
    return min(pool, key=lambda m: m.cost_per_1k), "simple prompt -> cheapest"


@dataclass
class RouteResult:
    model: str
    provider: str
    reason: str
    text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    attempts: list[str]


async def route(prompt: str, strategy: str | None = None, model: str | None = None,
                max_tokens: int = 512) -> RouteResult:
    strategy = strategy or settings.default_strategy
    first, reason = choose(prompt, strategy, model)

    # primary first, then the fallback chain (skipping dupes and unavailable)
    chain = [first] + [BY_NAME[n] for n in settings.fallback_chain
                       if n in BY_NAME and n != first.name and settings.has_key(BY_NAME[n].provider)]
    attempts: list[str] = []
    for spec in chain:
        provider = REGISTRY[spec.provider](
            getattr(settings, f"{spec.provider}_key", None), settings.request_timeout_s)
        t0 = time.perf_counter()
        try:
            c: Completion = await provider.complete(spec.model_id, prompt, max_tokens)
        except Exception as e:  # noqa: BLE001 - any failure triggers fallback
            attempts.append(f"{spec.name}: FAILED ({type(e).__name__}: {e})")
            continue
        attempts.append(f"{spec.name}: ok")
        cost = (c.input_tokens + c.output_tokens) / 1000 * spec.cost_per_1k
        return RouteResult(spec.name, spec.provider,
                           reason if spec is first else f"fallback after: {attempts[0]}",
                           c.text, c.input_tokens, c.output_tokens, round(cost, 6),
                           int((time.perf_counter() - t0) * 1000), attempts)
    raise RuntimeError("all models failed: " + "; ".join(attempts))
