"""
pipeline.py - Trade Intelligence Pipeline Orchestrator
========================================================
Orchestrates all quant intelligence layers in sequence.
If any critical step fails -> skip trade.

Pipeline:
1. Market Regime Detection
2. Liquidity Sweep / Dark Pool Detection
3. Market Maker Model (Order Block)
4. Options Flow Analysis
5. Gamma Exposure Alignment
6. Strategy Signal
7. AI Prediction Model
8. Trade Ranking
9. Risk Check
10. Contract Resolution
11. Trade Execution
"""
import logging
from datetime import datetime, timezone, timedelta

from market.options_flow import analyze_options_flow
from market.dark_pool_detector import detect_dark_pool_zones, is_near_accumulation_zone
from market.correlation_filter import check_correlation
from ai.market_predictor import predict_market_direction
from ai.trade_ranker import rank_trade, MIN_RANK_SCORE
from risk.hedging_engine import analyze_portfolio_exposure

logger = logging.getLogger("quant_pipeline")

# Trade frequency controls
MAX_TRADES_PER_DAY = 4
MAX_CONSECUTIVE_LOSSES = 3
DAILY_DRAWDOWN_LIMIT_PCT = 4.0
MIN_RR_RATIO = 2.0

# Trading time window
TRADE_START_HOUR = 9
TRADE_START_MIN = 30
TRADE_END_HOUR = 14
TRADE_END_MIN = 45


def get_ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


def is_quant_trading_hours():
    """Check if within quant trading window (09:30 - 14:45 IST)."""
    now = get_ist_now()
    if now.weekday() >= 5:
        return False
    start = now.replace(hour=TRADE_START_HOUR, minute=TRADE_START_MIN, second=0, microsecond=0)
    end = now.replace(hour=TRADE_END_HOUR, minute=TRADE_END_MIN, second=0, microsecond=0)
    return start <= now <= end


def check_frequency_limits(trades_today, consecutive_losses, daily_pnl, portfolio_value):
    """
    Check trade frequency and drawdown limits.

    Returns:
        (allowed, reason)
    """
    if trades_today >= MAX_TRADES_PER_DAY:
        return False, f"Max trades/day reached ({MAX_TRADES_PER_DAY})"

    if consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
        return False, f"Max consecutive losses reached ({MAX_CONSECUTIVE_LOSSES})"

    if portfolio_value > 0:
        drawdown_pct = abs(min(0, daily_pnl)) / portfolio_value * 100
        if drawdown_pct >= DAILY_DRAWDOWN_LIMIT_PCT:
            return False, f"Daily drawdown {drawdown_pct:.1f}% >= {DAILY_DRAWDOWN_LIMIT_PCT}% limit"

    return True, "OK"


def validate_risk_reward(entry, stop_loss, target, action):
    """Check if trade meets minimum 1:2 risk-reward ratio."""
    if action == "BUY":
        risk = entry - stop_loss
        reward = target - entry
    else:
        risk = stop_loss - entry
        reward = entry - target

    if risk <= 0:
        return False, 0, "Invalid risk (SL >= entry)"

    rr_ratio = reward / risk
    if rr_ratio < MIN_RR_RATIO:
        return False, round(rr_ratio, 2), f"R:R {rr_ratio:.1f} below minimum {MIN_RR_RATIO}"

    return True, round(rr_ratio, 2), f"R:R {rr_ratio:.1f} meets {MIN_RR_RATIO} minimum"


def run_pipeline(
    symbol,
    prices,
    volumes,
    vwap,
    signal_data,
    market_regime,
    market_data_dict,
    open_positions,
    trades_today_count,
    consecutive_losses,
    daily_pnl,
    portfolio_value,
    entry_price=None,
    stop_loss=None,
    target_price=None,
):
    """
    Run the full Trade Intelligence Pipeline.

    Returns:
        dict with pipeline_result (PASS/FAIL), steps, trade_rank, reasoning
    """
    action = signal_data.get("action", "HOLD")
    pipeline_steps = []

    # Step 0: Action Check
    if action == "HOLD":
        return _result("SKIP", pipeline_steps, "No signal (HOLD)", 0)

    # Step 1: TIME FILTER
    time_ok = is_quant_trading_hours()
    pipeline_steps.append({
        "step": 1, "name": "Time Filter",
        "passed": time_ok,
        "details": f"Window: {TRADE_START_HOUR}:{TRADE_START_MIN:02d}-{TRADE_END_HOUR}:{TRADE_END_MIN:02d} IST",
    })
    if not time_ok:
        return _result("FAIL", pipeline_steps, "Outside trading hours (09:30-14:45)", 0)

    # Step 2: FREQUENCY LIMITS
    freq_ok, freq_reason = check_frequency_limits(
        trades_today_count, consecutive_losses, daily_pnl, portfolio_value
    )
    pipeline_steps.append({
        "step": 2, "name": "Frequency Control",
        "passed": freq_ok,
        "details": freq_reason,
        "data": {
            "trades_today": trades_today_count,
            "max_trades": MAX_TRADES_PER_DAY,
            "consecutive_losses": consecutive_losses,
            "max_consec_losses": MAX_CONSECUTIVE_LOSSES,
        },
    })
    if not freq_ok:
        return _result("FAIL", pipeline_steps, freq_reason, 0)

    # Step 3: MARKET REGIME
    regime_upper = market_regime.upper() if market_regime else "UNKNOWN"
    regime_ok = True
    regime_detail = f"Regime: {regime_upper}"
    # Block trades in extreme conditions
    if "UNKNOWN" in regime_upper or regime_upper == "":
        regime_ok = False
        regime_detail = "Cannot determine market regime"
    pipeline_steps.append({
        "step": 3, "name": "Market Regime",
        "passed": regime_ok,
        "details": regime_detail,
    })
    if not regime_ok:
        return _result("FAIL", pipeline_steps, regime_detail, 0)

    # Step 4: DARK POOL / LIQUIDITY SWEEP
    dark_pool = detect_dark_pool_zones(prices, volumes, vwap, symbol)
    dp_passed = True
    dp_detail = f"Zones: {dark_pool['total_zones_detected']}, Type: {dark_pool['zone_type']}"
    # Favor accumulation for buys, distribution for sells
    if dark_pool["zone_type"] == "distribution" and action == "BUY" and dark_pool["confidence"] > 70:
        dp_passed = False
        dp_detail = f"Distribution zone detected (conf={dark_pool['confidence']}%), contra to BUY"
    elif dark_pool["zone_type"] == "accumulation" and action == "SELL" and dark_pool["confidence"] > 70:
        dp_passed = False
        dp_detail = f"Accumulation zone detected (conf={dark_pool['confidence']}%), contra to SELL"
    pipeline_steps.append({
        "step": 4, "name": "Dark Pool Detection",
        "passed": dp_passed,
        "details": dp_detail,
        "data": {
            "zone_type": dark_pool["zone_type"],
            "confidence": dark_pool["confidence"],
            "institutional": dark_pool["institutional_activity"],
        },
    })
    if not dp_passed:
        return _result("FAIL", pipeline_steps, dp_detail, 0)

    # Step 5: OPTIONS FLOW
    options_flow = analyze_options_flow(prices, volumes, symbol)
    of_passed = True
    of_detail = f"Signal: {options_flow['signal']}, Strength: {options_flow['strength']}"
    # Contra-flow blocks trade
    if options_flow["signal"] == "bearish_flow" and action == "BUY" and options_flow["strength"] > 50:
        of_passed = False
        of_detail = f"Strong bearish flow ({options_flow['strength']}) contra to BUY"
    elif options_flow["signal"] == "bullish_flow" and action == "SELL" and options_flow["strength"] > 50:
        of_passed = False
        of_detail = f"Strong bullish flow ({options_flow['strength']}) contra to SELL"
    pipeline_steps.append({
        "step": 5, "name": "Options Flow Analysis",
        "passed": of_passed,
        "details": of_detail,
        "data": {
            "signal": options_flow["signal"],
            "strength": options_flow["strength"],
            "unusual": options_flow["unusual_activity"],
        },
    })
    if not of_passed:
        return _result("FAIL", pipeline_steps, of_detail, 0)

    # Step 6: CORRELATION FILTER
    corr = check_correlation(symbol, action, market_data_dict)
    corr_passed = corr.get("confirmation", True)
    corr_detail = f"Strength: {corr['correlation_strength']}, Confirmed: {corr['pairs_confirmed']}/{corr['pairs_checked']}"
    # Only block if strong contradiction
    if not corr_passed and corr["correlation_strength"] < 20:
        corr_passed = False
        corr_detail = f"Correlation rejection: only {corr['pairs_confirmed']}/{corr['pairs_checked']} confirmed"
    else:
        corr_passed = True  # Allow weak correlation mismatches through
    pipeline_steps.append({
        "step": 6, "name": "Correlation Filter",
        "passed": corr_passed,
        "details": corr_detail,
        "data": corr,
    })
    if not corr_passed:
        return _result("FAIL", pipeline_steps, corr_detail, 0)

    # Step 7: AI PREDICTION
    ai_pred = predict_market_direction(prices, volumes, vwap, market_regime)
    ai_passed = ai_pred.get("trade_allowed", False)
    ai_detail = f"Prediction: {ai_pred['predicted_direction']}, Confidence: {ai_pred['confidence']}%"
    # Allow through if prediction is neutral but don't block
    if ai_pred["predicted_direction"] == "neutral":
        ai_passed = True
        ai_detail += " (neutral - allowing)"
    # Block if AI contradicts with high confidence
    elif (ai_pred["predicted_direction"] == "bearish" and action == "BUY" and ai_pred["confidence"] > 70) or \
         (ai_pred["predicted_direction"] == "bullish" and action == "SELL" and ai_pred["confidence"] > 70):
        ai_passed = False
        ai_detail = f"AI contradicts {action}: {ai_pred['predicted_direction']} at {ai_pred['confidence']}% conf"
    elif ai_pred["confidence"] >= 65:
        ai_passed = True
    pipeline_steps.append({
        "step": 7, "name": "AI Prediction",
        "passed": ai_passed,
        "details": ai_detail,
        "data": {
            "direction": ai_pred["predicted_direction"],
            "confidence": ai_pred["confidence"],
            "factors_count": len(ai_pred.get("factors", {})),
        },
    })
    if not ai_passed:
        return _result("FAIL", pipeline_steps, ai_detail, 0)

    # Step 8: RISK-REWARD CHECK
    if entry_price and stop_loss and target_price:
        rr_ok, rr_ratio, rr_detail = validate_risk_reward(entry_price, stop_loss, target_price, action)
    else:
        rr_ok = True
        rr_ratio = 0
        rr_detail = "R:R not calculated (no entry/SL/target)"
    pipeline_steps.append({
        "step": 8, "name": "Risk-Reward Check",
        "passed": rr_ok,
        "details": rr_detail,
        "data": {"ratio": rr_ratio, "minimum": MIN_RR_RATIO},
    })
    if not rr_ok:
        return _result("FAIL", pipeline_steps, rr_detail, 0)

    # Step 9: TRADE RANKING
    trade_rank = rank_trade(
        signal_data=signal_data,
        options_flow_data=options_flow,
        dark_pool_data=dark_pool,
        ai_prediction_data=ai_pred,
        correlation_data=corr,
        market_regime=market_regime,
    )
    rank_passed = trade_rank["trade_allowed"]
    rank_detail = f"Score: {trade_rank['total_score']}/100 (min={MIN_RANK_SCORE}), Grade: {trade_rank['grade']}"
    pipeline_steps.append({
        "step": 9, "name": "Trade Ranking",
        "passed": rank_passed,
        "details": rank_detail,
        "data": trade_rank["components"],
    })
    if not rank_passed:
        return _result("FAIL", pipeline_steps, f"Trade rank {trade_rank['total_score']} < {MIN_RANK_SCORE}", trade_rank["total_score"])

    # Step 10: HEDGING CHECK
    hedge = analyze_portfolio_exposure(open_positions, portfolio_value)
    hedge_detail = f"Exposure: {hedge['net_exposure']}, Hedge needed: {hedge['hedge_needed']}"
    pipeline_steps.append({
        "step": 10, "name": "Portfolio Hedge Check",
        "passed": True,  # Info only, doesn't block
        "details": hedge_detail,
        "data": {
            "bullish_pct": hedge["bullish_exposure_pct"],
            "bearish_pct": hedge["bearish_exposure_pct"],
            "hedge_needed": hedge["hedge_needed"],
        },
    })

    # ALL STEPS PASSED
    return _result(
        "PASS",
        pipeline_steps,
        f"All checks passed. Rank: {trade_rank['total_score']}/{trade_rank['max_score']} ({trade_rank['grade']})",
        trade_rank["total_score"],
        trade_rank=trade_rank,
        ai_prediction=ai_pred,
        options_flow=options_flow,
        dark_pool=dark_pool,
        correlation=corr,
        hedge=hedge,
    )


def _result(status, steps, reason, score, **extra):
    return {
        "pipeline_result": status,
        "steps": steps,
        "steps_passed": len([s for s in steps if s["passed"]]),
        "steps_total": len(steps),
        "reason": reason,
        "trade_score": score,
        "timestamp": get_ist_now().isoformat(),
        **extra,
    }
