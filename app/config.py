"""Central config. Everything comes from env vars so the same image runs
in Docker, Kubernetes (ConfigMap/Secret) and Lambda (function env)."""
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelSpec:
    name: str            # logical name used by the router, e.g. "fast"
    provider: str        # openai | anthropic | gemini | mock
    model_id: str        # provider model string
    cost_per_1k: float   # USD per 1K tokens (blended, for routing decisions)
    quality: int         # 1-10 rough quality score
    max_context: int     # tokens


# Edit this catalog to experiment with routing. Prices are illustrative only.
CATALOG: list[ModelSpec] = [
    ModelSpec("mock-fast", "mock", "mock-fast", 0.0001, 3, 8_000),
    ModelSpec("mock-smart", "mock", "mock-smart", 0.002, 8, 200_000),
    ModelSpec("gpt-mini", "openai", os.getenv("OPENAI_MODEL", "gpt-4o-mini"), 0.0004, 6, 128_000),
    ModelSpec("claude", "anthropic", os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5"), 0.003, 9, 200_000),
    ModelSpec("gemini", "gemini", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), 0.0003, 6, 1_000_000),
]


@dataclass
class Settings:
    default_strategy: str = os.getenv("ROUTER_STRATEGY", "rules")
    request_timeout_s: float = float(os.getenv("REQUEST_TIMEOUT_S", "30"))
    openai_key: str | None = os.getenv("OPENAI_API_KEY")
    anthropic_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    gemini_key: str | None = os.getenv("GEMINI_API_KEY")
    # Comma-separated fallback order, used when a model call fails
    fallback_chain: list[str] = field(default_factory=lambda: os.getenv(
        "FALLBACK_CHAIN", "claude,gpt-mini,gemini,mock-smart").split(","))

    def has_key(self, provider: str) -> bool:
        return provider == "mock" or bool(getattr(self, f"{provider}_key", None))


settings = Settings()
