import json

from agent.minimax_brain import ask_minimax, parse_json_response
from config import MINIMAX_API_KEY


class AISignalValidator:
    def __init__(self, min_confidence: int = 70):
        self.min_confidence = min_confidence

    def validate(self, payload: dict) -> dict:
        heuristic = self._heuristic_score(payload)
        if not MINIMAX_API_KEY:
            return {
                "allowed": heuristic >= self.min_confidence,
                "confidence": heuristic,
                "summary": "Heuristic validation (MiniMax unavailable)",
                "source": "heuristic",
            }

        prompt = {
            "symbol": payload.get("symbol"),
            "strategy": payload.get("strategy"),
            "market_regime": payload.get("market_regime"),
            "signal": payload.get("signal"),
            "volume_ratio": payload.get("volume_ratio"),
            "risk_reward": payload.get("risk_reward"),
            "recent_candles": payload.get("recent_candles", [])[-20:],
        }
        raw = ask_minimax(
            "Return JSON only with keys confidence, allowed, summary. "
            f"Evaluate this trade setup: {json.dumps(prompt)}",
            web_search=False,
        )
        parsed = parse_json_response(raw)
        confidence = int(parsed.get("confidence", heuristic)) if parsed else heuristic
        return {
            "allowed": confidence >= self.min_confidence,
            "confidence": confidence,
            "summary": parsed.get("summary", "MiniMax validation complete") if parsed else "MiniMax fallback to heuristic",
            "source": "minimax" if parsed else "heuristic",
        }

    def _heuristic_score(self, payload: dict) -> int:
        regime = payload.get("market_regime", {})
        signal = payload.get("signal", {})
        score = 55
        score += min(15, int(regime.get("trend_strength", 0) / 8))
        score += min(12, int((payload.get("volume_ratio", 1.0) - 1.0) * 20))
        score += min(10, int(max(payload.get("risk_reward", 0) - 1.0, 0) * 10))
        score += int(signal.get("strategy_confidence", 70) / 10)
        if regime.get("sideways"):
            score -= 12
        if regime.get("high_volatility"):
            score -= 5
        return max(0, min(100, score))
