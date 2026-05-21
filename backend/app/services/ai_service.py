"""
NEXUS ATLAS — Unified AI service.

Wraps Groq (Llama 3.3 70B) for natural-language interpretation of geospatial
scans, anomalies, and tactical recommendations. Designed to fail gracefully:
when GROQ_API_KEY is not set, every public method returns None and callers
fall back to the deterministic template responses.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


SYSTEM_PROMPT_ANALYST = (
    "You are NEXUS ATLAS, an elite geospatial intelligence AI inspired by "
    "Jarvis and military OSINT systems. You produce concise, tactical, "
    "structured assessments. Style: confident, technical, no fluff. "
    "Always reference coordinates, severity, and operational implications. "
    "Output MUST be valid JSON when asked for JSON."
)


class AIService:
    """Lazy singleton-style wrapper around the Groq async client."""

    _instance: Optional["AIService"] = None

    def __init__(self) -> None:
        self.model = settings.GROQ_MODEL
        self.client = None
        self._init_error: Optional[str] = None

        if not settings.GROQ_API_KEY:
            self._init_error = "GROQ_API_KEY not configured"
            return

        try:
            from groq import AsyncGroq

            self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            logger.info(f"[AI] Groq client initialized (model={self.model})")
        except ImportError:
            self._init_error = "groq package not installed"
            logger.warning("[AI] groq SDK missing — install `pip install groq`")
        except Exception as e:  # pragma: no cover
            self._init_error = f"Groq init failed: {e}"
            logger.error(f"[AI] {self._init_error}")

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------

    @classmethod
    def instance(cls) -> "AIService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_configured(self) -> bool:
        return self.client is not None

    @property
    def status(self) -> dict[str, Any]:
        return {
            "configured": self.is_configured,
            "provider": "groq",
            "model": self.model,
            "error": self._init_error,
        }

    async def chat(
        self,
        user_message: str,
        system_message: str = SYSTEM_PROMPT_ANALYST,
        max_tokens: int = 800,
        temperature: float = 0.4,
        json_mode: bool = False,
    ) -> Optional[str]:
        """Send a single-turn chat. Returns None if not configured or on error."""
        if not self.client:
            return None
        try:
            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            resp = await self.client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"[AI] chat failed: {e}")
            return None

    # ------------------------------------------------------------------
    # High-level helpers
    # ------------------------------------------------------------------

    async def interpret_scan(
        self,
        scan: Any,
        anomalies: list,
        threat_level: str,
    ) -> Optional[dict[str, Any]]:
        """Generate AI analysis + recommendations for a completed scan.

        Returns dict with keys: `analysis` (str), `recommendations` (list[str]),
        `headline` (str). None if AI unavailable.
        """
        if not self.client:
            return None

        anomaly_lines = []
        for a in anomalies[:25]:  # cap context
            anomaly_lines.append(
                f"- [{a.severity:>8s}] {a.anomaly_type} @ "
                f"({a.latitude:.4f}, {a.longitude:.4f}) "
                f"conf={a.confidence:.2f} — {a.description or 'no description'}"
            )
        anomaly_block = "\n".join(anomaly_lines) if anomaly_lines else "(none detected)"

        prompt = (
            f"Scan target: {getattr(scan, 'name', 'unnamed')}\n"
            f"Bounds: lat [{scan.lat_min:.4f}, {scan.lat_max:.4f}], "
            f"lon [{scan.lon_min:.4f}, {scan.lon_max:.4f}]\n"
            f"Scan type: {getattr(scan, 'scan_type', 'full')}\n"
            f"Computed threat level: {threat_level.upper()}\n"
            f"Anomaly count: {len(anomalies)}\n\n"
            f"Detected anomalies:\n{anomaly_block}\n\n"
            "Produce a tactical intelligence assessment as a JSON object with this exact schema:\n"
            "{\n"
            '  "headline": "<one-line callsign-style headline, <=12 words>",\n'
            '  "analysis": "<3-5 paragraph tactical assessment, ~250 words>",\n'
            '  "recommendations": ["<directive 1>", "<directive 2>", ...]  // 3-6 imperative items\n'
            "}\n"
            "Do not include any text outside the JSON object."
        )

        raw = await self.chat(prompt, max_tokens=1200, json_mode=True)
        if not raw:
            return None
        return _safe_json_parse(raw)

    async def interpret_coordinate(
        self,
        lat: float,
        lon: float,
        radius_km: float,
        terrain_type: str,
        risk_factors: list[str],
    ) -> Optional[str]:
        """Generate a short tactical readout for a single coordinate query."""
        if not self.client:
            return None

        prompt = (
            f"Coordinate query: ({lat:.4f}, {lon:.4f}) with {radius_km:.1f} km radius.\n"
            f"Classified terrain: {terrain_type}\n"
            f"Risk factors: {', '.join(risk_factors) if risk_factors else 'nominal'}\n\n"
            "In 2-3 sentences, give a tactical readout: what an operator should know "
            "about this region before deploying a scan. Mention notable environmental, "
            "geopolitical, or geological considerations if relevant. Be specific."
        )
        return await self.chat(prompt, max_tokens=300, temperature=0.5)

    async def free_query(self, question: str, context: str = "") -> Optional[str]:
        """For the in-dashboard console terminal."""
        if not self.client:
            return None
        prompt = question if not context else f"Context:\n{context}\n\nQuestion: {question}"
        return await self.chat(prompt, max_tokens=600)


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------


def _safe_json_parse(raw: str) -> Optional[dict[str, Any]]:
    """Parse JSON from an LLM response, tolerating code fences and stray text."""
    text = raw.strip()
    # Strip ```json fences if present
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract the first JSON object substring
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return None


def get_ai_service() -> AIService:
    """FastAPI-friendly accessor."""
    return AIService.instance()
