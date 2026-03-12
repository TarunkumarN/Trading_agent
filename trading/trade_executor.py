from dataclasses import asdict

import pandas as pd
import ta

from ai.ai_signal_validator import AISignalValidator
from analytics.trade_score import score_trade
from config import RISK_REWARD_RATIO
from market.market_regime import detect_market_regime
from strategies import auction_strategy, breakout_strategy, commodity_strategy, fno_strategy, vwap_strategy

FNO_TOKENS = ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "CE", "PE", "FUT")


class TradeExecutor:
    def __init__(self, min_trade_score: float = 80.0, min_volume_ratio: float = 1.1):
        self.min_trade_score = min_trade_score
        self.min_volume_ratio = min_volume_ratio
        self.ai_validator = AISignalValidator(min_confidence=70)

    def evaluate_symbol(self, symbol: str, prices: list[float], highs: list[float], lows: list[float], volumes: list[float], vwap: float, market_bias_pct: float = 0.0):
        if len(prices) < 50 or len(highs) < 50 or len(lows) < 50 or len(volumes) < 50:
            return {"allowed": False, "reason": "Need at least 50 candles", "symbol": symbol}

        current_price = float(prices[-1])
        avg_volume = sum(volumes[-20:]) / min(len(volumes), 20) if volumes else 0.0
        current_volume = float(volumes[-1]) if volumes else 0.0
        volume_ratio = (current_volume / avg_volume) if avg_volume else 0.0
        liquidity = self._liquidity_check(current_price, current_volume, volume_ratio)
        if not liquidity["allowed"]:
            return {"allowed": False, "reason": liquidity["reason"], "symbol": symbol}

        regime = detect_market_regime(prices, highs, lows, volumes, vwap=vwap, bias_pct=market_bias_pct)
        if regime.regime == "INSUFFICIENT_DATA" or regime.sideways:
            return {
                "allowed": False,
                "reason": f"Market regime blocked: {regime.regime}",
                "symbol": symbol,
                "market_regime": regime.to_dict(),
            }

        context = self._build_context(symbol, prices, highs, lows, volumes, vwap, regime, volume_ratio)
        candidates = []
        for strategy_module in self._strategy_modules(symbol):
            try:
                candidate = strategy_module.evaluate(context)
            except Exception as exc:
                candidate = None
                context.setdefault("errors", []).append(f"{strategy_module.__name__}: {exc}")
            if not candidate:
                continue
            enriched = self._enrich_candidate(symbol, candidate, context, regime, volume_ratio, liquidity)
            if enriched["allowed"]:
                candidates.append(enriched)

        if not candidates:
            return {
                "allowed": False,
                "reason": "No strategy passed all filters",
                "symbol": symbol,
                "market_regime": regime.to_dict(),
                "liquidity": liquidity,
            }

        best = max(candidates, key=lambda item: (item["trade_score"], item["ai_confidence"], item["strategy_confidence"]))
        return best

    def _build_context(self, symbol, prices, highs, lows, volumes, vwap, regime, volume_ratio):
        df = pd.DataFrame({"close": prices, "high": highs, "low": lows, "volume": volumes})
        rsi_series = ta.momentum.rsi(df["close"], window=14)
        current_price = float(prices[-1])
        atr = float(regime.atr or 0.0)
        return {
            "symbol": symbol,
            "prices": prices,
            "highs": highs,
            "lows": lows,
            "volumes": volumes,
            "current_price": current_price,
            "vwap": float(vwap or 0.0),
            "atr": atr,
            "rsi": float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0,
            "vol_ratio": round(volume_ratio, 2),
            "market_regime": regime,
        }

    def _strategy_modules(self, symbol: str):
        modules = [breakout_strategy, vwap_strategy, auction_strategy]
        if self._is_fno_symbol(symbol):
            modules.insert(0, fno_strategy)
        if commodity_strategy.supports(symbol):
            modules.insert(0, commodity_strategy)
        return modules

    def _enrich_candidate(self, symbol, candidate, context, regime, volume_ratio, liquidity):
        entry = float(candidate["entry"])
        stop_loss = float(candidate["stop_loss"])
        target = float(candidate["target"])
        risk = abs(entry - stop_loss)
        reward = abs(target - entry)
        risk_reward = round((reward / risk), 2) if risk else 0.0
        recent_candles = self._recent_candles(context)
        ai_result = self.ai_validator.validate({
            "symbol": symbol,
            "strategy": candidate["strategy"],
            "market_regime": regime.to_dict(),
            "signal": candidate,
            "volume_ratio": volume_ratio,
            "risk_reward": risk_reward,
            "recent_candles": recent_candles,
        })
        trade_quality = score_trade(
            trend_strength=regime.trend_strength,
            volume_ratio=volume_ratio,
            ai_confidence=ai_result["confidence"],
            risk_reward_ratio=risk_reward,
            liquidity_score=liquidity["score"],
        )
        allowed = (
            ai_result["allowed"]
            and trade_quality["allowed"]
            and liquidity["allowed"]
            and risk_reward >= RISK_REWARD_RATIO
        )
        return {
            **candidate,
            "symbol": symbol,
            "allowed": allowed,
            "trade_score": trade_quality["score"],
            "trade_score_components": trade_quality["components"],
            "ai_confidence": ai_result["confidence"],
            "ai_allowed": ai_result["allowed"],
            "ai_summary": ai_result["summary"],
            "ai_source": ai_result["source"],
            "market_regime": regime.to_dict(),
            "liquidity": liquidity,
            "risk_reward": risk_reward,
            "volume_ratio": round(volume_ratio, 2),
            "strategy_confidence": int(candidate.get("strategy_confidence", 70)),
            "rejection_reason": None if allowed else self._rejection_reason(ai_result, trade_quality, liquidity, risk_reward),
        }

    def _recent_candles(self, context):
        candles = []
        for close, high, low, volume in zip(
            context["prices"][-50:],
            context["highs"][-50:],
            context["lows"][-50:],
            context["volumes"][-50:],
        ):
            candles.append({
                "close": round(float(close), 2),
                "high": round(float(high), 2),
                "low": round(float(low), 2),
                "volume": round(float(volume), 2),
            })
        return candles

    def _liquidity_check(self, current_price: float, current_volume: float, volume_ratio: float):
        score = 0.0
        if current_price > 50:
            score += 3
        if current_volume >= 10000:
            score += 4
        elif current_volume >= 3000:
            score += 2
        if volume_ratio >= 1.5:
            score += 3
        elif volume_ratio >= self.min_volume_ratio:
            score += 2

        allowed = current_price > 0 and current_volume > 0 and volume_ratio >= self.min_volume_ratio
        reason = "OK" if allowed else f"Liquidity weak: vol_ratio={volume_ratio:.2f}, volume={current_volume:.0f}"
        return {"allowed": allowed, "score": round(min(score, 10.0), 2), "reason": reason}

    def _is_fno_symbol(self, symbol: str) -> bool:
        upper = symbol.upper()
        return any(token in upper for token in FNO_TOKENS)

    def _rejection_reason(self, ai_result, trade_quality, liquidity, risk_reward):
        if not liquidity["allowed"]:
            return liquidity["reason"]
        if risk_reward < RISK_REWARD_RATIO:
            return f"Risk reward {risk_reward:.2f} below {RISK_REWARD_RATIO:.2f}"
        if not ai_result["allowed"]:
            return f"AI confidence {ai_result['confidence']} below threshold"
        if not trade_quality["allowed"]:
            return f"Trade score {trade_quality['score']} below threshold"
        return "Unknown filter rejection"
