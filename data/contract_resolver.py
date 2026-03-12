import logging
from datetime import date, datetime, timedelta

from kiteconnect import KiteConnect

from config import (
    COMMODITY_PRICE_FALLBACK_PCT,
    FNO_PRICE_FALLBACK_PCT,
    KITE_ACCESS_TOKEN,
    KITE_API_KEY,
)

logger = logging.getLogger(__name__)

_CACHE_TTL = timedelta(minutes=15)
_instrument_cache = {}

_OPTION_STEPS = {
    "NIFTY": 50,
    "BANKNIFTY": 100,
    "FINNIFTY": 50,
    "MIDCPNIFTY": 25,
    "SENSEX": 100,
}

_COMMODITY_ALIASES = {
    "CRUDE": "CRUDEOIL",
    "OIL": "CRUDEOIL",
    "GOLD": "GOLD",
    "SILVER": "SILVER",
}


def resolve_trade_contract(symbol: str, spot_price: float, instrument_type: str, option_side: str | None = None):
    instrument_type = (instrument_type or "EQUITY").upper()
    if instrument_type == "FNO":
        return _resolve_option_contract(symbol, spot_price, option_side)
    if instrument_type == "COMMODITY":
        return _resolve_commodity_contract(symbol, spot_price)
    return {
        "underlying_symbol": symbol,
        "tradingsymbol": symbol,
        "exchange": "NSE",
        "instrument_type": "EQUITY",
        "contract_price": round(float(spot_price), 2),
        "lot_size": 1,
        "expiry": None,
        "price_source": "spot",
    }


def get_live_price(tradingsymbol: str, exchange: str) -> float | None:
    quote_key = f"{exchange}:{tradingsymbol}"
    kite = _get_kite()
    if not kite:
        return None
    try:
        quote = kite.quote([quote_key]).get(quote_key, {})
        price = quote.get("last_price")
        if price and price > 0:
            return float(price)
    except Exception as exc:
        logger.warning("Quote fetch failed for %s: %s", quote_key, exc)
    return None


def derive_contract_levels(contract_price: float, spot_entry: float, spot_stop: float, spot_target: float, action: str, instrument_type: str):
    contract_price = float(contract_price)
    spot_entry = float(spot_entry)
    spot_stop = float(spot_stop)
    spot_target = float(spot_target)
    if contract_price <= 0 or spot_entry <= 0:
        return 0.0, 0.0

    if instrument_type.upper() == "FNO":
        risk_pct = abs(spot_entry - spot_stop) / spot_entry if spot_entry else 0.0
        reward_pct = abs(spot_target - spot_entry) / spot_entry if spot_entry else 0.0
        stop_pct = min(max(risk_pct * 2.0, 0.12), 0.35)
        target_pct = min(max(reward_pct * 2.0, 0.25), 0.8)
        contract_stop = round(contract_price * (1 - stop_pct), 2)
        contract_target = round(contract_price * (1 + target_pct), 2)
        return contract_stop, contract_target

    scale = contract_price / spot_entry
    if action == "BUY":
        contract_stop = round(contract_price - abs(spot_entry - spot_stop) * scale, 2)
        contract_target = round(contract_price + abs(spot_target - spot_entry) * scale, 2)
    else:
        contract_stop = round(contract_price + abs(spot_stop - spot_entry) * scale, 2)
        contract_target = round(contract_price - abs(spot_entry - spot_target) * scale, 2)
    return contract_stop, contract_target


def lot_aligned_quantity(qty: int, lot_size: int) -> int:
    if lot_size <= 1:
        return max(qty, 0)
    return max((qty // lot_size) * lot_size, 0)


def _resolve_option_contract(symbol: str, spot_price: float, option_side: str | None):
    underlying = _normalize_underlying(symbol)
    side = "CE" if (option_side or "").upper() == "CALL" else "PE"
    instruments = _get_instruments("NFO")
    if instruments:
        matches = [
            inst for inst in instruments
            if inst.get("name") == underlying
            and inst.get("instrument_type") == side
            and inst.get("expiry")
            and inst["expiry"] >= date.today()
        ]
        if matches:
            nearest_expiry = min(inst["expiry"] for inst in matches)
            expiry_matches = [inst for inst in matches if inst["expiry"] == nearest_expiry]
            target_strike = _nearest_strike(underlying, spot_price)
            selected = min(expiry_matches, key=lambda inst: abs(float(inst.get("strike") or 0.0) - target_strike))
            premium = get_live_price(selected["tradingsymbol"], "NFO") or _fallback_price(spot_price, FNO_PRICE_FALLBACK_PCT)
            return {
                "underlying_symbol": underlying,
                "tradingsymbol": selected["tradingsymbol"],
                "exchange": "NFO",
                "instrument_type": "FNO",
                "contract_price": round(float(premium), 2),
                "lot_size": int(selected.get("lot_size") or 1),
                "expiry": selected["expiry"].isoformat(),
                "strike": float(selected.get("strike") or 0.0),
                "option_type": side,
                "price_source": "quote" if premium else "fallback",
            }

    fallback_price = _fallback_price(spot_price, FNO_PRICE_FALLBACK_PCT)
    strike = _nearest_strike(underlying, spot_price)
    return {
        "underlying_symbol": underlying,
        "tradingsymbol": f"{underlying}_{strike:.0f}{side}",
        "exchange": "NFO",
        "instrument_type": "FNO",
        "contract_price": fallback_price,
        "lot_size": _default_lot_size(underlying),
        "expiry": None,
        "strike": strike,
        "option_type": side,
        "price_source": "fallback",
    }


def _resolve_commodity_contract(symbol: str, spot_price: float):
    underlying = _normalize_commodity(symbol)
    instruments = _get_instruments("MCX")
    if instruments:
        matches = [
            inst for inst in instruments
            if inst.get("name") == underlying
            and inst.get("expiry")
            and inst["expiry"] >= date.today()
        ]
        if matches:
            selected = min(matches, key=lambda inst: inst["expiry"])
            price = get_live_price(selected["tradingsymbol"], "MCX") or _fallback_price(spot_price, COMMODITY_PRICE_FALLBACK_PCT)
            return {
                "underlying_symbol": underlying,
                "tradingsymbol": selected["tradingsymbol"],
                "exchange": "MCX",
                "instrument_type": "COMMODITY",
                "contract_price": round(float(price), 2),
                "lot_size": int(selected.get("lot_size") or 1),
                "expiry": selected["expiry"].isoformat(),
                "price_source": "quote" if price else "fallback",
            }

    fallback_price = _fallback_price(spot_price, COMMODITY_PRICE_FALLBACK_PCT)
    return {
        "underlying_symbol": underlying,
        "tradingsymbol": underlying,
        "exchange": "MCX",
        "instrument_type": "COMMODITY",
        "contract_price": fallback_price,
        "lot_size": 1,
        "expiry": None,
        "price_source": "fallback",
    }


def _get_instruments(exchange: str):
    now = datetime.now()
    cached = _instrument_cache.get(exchange)
    if cached and now - cached["loaded_at"] < _CACHE_TTL:
        return cached["instruments"]
    kite = _get_kite()
    if not kite:
        return []
    try:
        instruments = kite.instruments(exchange)
        _instrument_cache[exchange] = {"loaded_at": now, "instruments": instruments}
        return instruments
    except Exception as exc:
        logger.warning("Instrument download failed for %s: %s", exchange, exc)
        return []


def _get_kite():
    if not KITE_API_KEY or not KITE_ACCESS_TOKEN:
        return None
    try:
        kite = KiteConnect(api_key=KITE_API_KEY)
        kite.set_access_token(KITE_ACCESS_TOKEN)
        return kite
    except Exception as exc:
        logger.warning("Kite initialisation failed: %s", exc)
        return None


def _normalize_underlying(symbol: str) -> str:
    upper = symbol.upper()
    for token in _OPTION_STEPS:
        if token in upper:
            return token
    return upper.replace("NSE:", "").replace("-I", "")


def _normalize_commodity(symbol: str) -> str:
    upper = symbol.upper()
    for token, canonical in _COMMODITY_ALIASES.items():
        if token in upper:
            return canonical
    return upper


def _nearest_strike(underlying: str, spot_price: float) -> float:
    step = _OPTION_STEPS.get(underlying, 100)
    if step <= 0:
        return round(spot_price, 0)
    return round(round(float(spot_price) / step) * step, 2)


def _fallback_price(spot_price: float, pct: float) -> float:
    return round(max(float(spot_price) * pct, 1.0), 2)


def _default_lot_size(underlying: str) -> int:
    defaults = {
        "NIFTY": 75,
        "BANKNIFTY": 35,
        "FINNIFTY": 65,
        "MIDCPNIFTY": 120,
        "SENSEX": 20,
    }
    return defaults.get(underlying, 25)
