"""
REMNANT — centralized configuration.

All environment-driven settings live here, validated at import time. A missing
required value is a clear startup error, never a silent mid-demo failure.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # --- core ---
    storage_path: str = field(default_factory=lambda: os.getenv("STORAGE_PATH", "./data/remnant.db"))
    host: str = field(default_factory=lambda: os.getenv("REMNANT_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("REMNANT_PORT", "8000")))

    # --- Minds integration ---
    mind_id: Optional[str] = field(default_factory=lambda: os.getenv("MIND_ID"))
    minds_api_key: Optional[str] = field(default_factory=lambda: os.getenv("MINDS_BUILDER_API_KEY"))

    # --- autonomous observation ---
    observatory_enabled: bool = field(default_factory=lambda: _env_bool("REMNANT_OBSERVATORY", True))
    observatory_interval_s: int = field(default_factory=lambda: int(os.getenv("REMNANT_OBSERVATORY_INTERVAL_S", "300")))
    observatory_cooldown_s: int = field(default_factory=lambda: int(os.getenv("REMNANT_OBSERVATORY_COOLDOWN_S", "86400")))

    # --- security ---
    cors_origins: list[str] = field(default_factory=lambda: [
        o.strip() for o in os.getenv("REMNANT_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()
    ])
    require_auth: bool = field(default_factory=lambda: _env_bool("REMNANT_REQUIRE_AUTH", False))
    api_token: Optional[str] = field(default_factory=lambda: os.getenv("REMNANT_API_TOKEN"))

    # --- log ---
    log_level: str = field(default_factory=lambda: os.getenv("REMNANT_LOG_LEVEL", "INFO"))

    @property
    def minds_configured(self) -> bool:
        return bool(self.mind_id and self.minds_api_key)

    def validate(self) -> None:
        """Fail fast: surface missing required config clearly."""
        if self.observatory_interval_s < 30:
            raise ValueError("REMNANT_OBSERVATORY_INTERVAL_S must be >= 30")
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"REMNANT_PORT out of range: {self.port}")
        if self.require_auth and not self.api_token:
            raise ValueError("REMNANT_REQUIRE_AUTH=true requires REMNANT_API_TOKEN")


settings = Settings()
settings.validate()