"""
contract_resolver.py - F&O Contract Resolution Engine
=======================================================
Resolves trading signals to proper F&O instruments.

Rules:
- Bullish signal → CE (Call Option)
- Bearish signal → PE (Put Option)

Returns:
- symbol (trading symbol with expiry)
- exchange (NFO/MCX)
- lot_size
- expiry
- strike_price
- option_type (CE/PE)
"""
import math
from datetime import datetime, timezone, timedelta


def get_ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


# F&O Lot sizes (as per NSE current specifications)
EQUITY_LOT_SIZES = {
    "RELIANCE": 250,
    "TCS": 150,
    "HDFCBANK": 550,
    "INFY": 300,
    "ICICIBANK": 700,
    "SBIN": 1500,
    "BAJFINANCE": 125,
    "ITC": 1600,
    "KOTAKBANK": 400,
    "LT": 150,
    "AXISBANK": 600,
    "ASIANPAINT": 300,
    "MARUTI": 50,
    "SUNPHARMA": 350,
    "WIPRO": 1500,
    "ULTRACEMCO": 100,
    "TITAN": 175,
    "HINDUNILVR": 300,
    "BHARTIARTL": 456,
    "NESTLEIND": 50,
    "POWERGRID": 2700,
    "NTPC": 2250,
    "ONGC": 3850,
    "JSWSTEEL": 675,
    "TATASTEEL": 3375,
}

INDEX_LOT_SIZES = {
    "NIFTY": 25,
    "BANKNIFTY": 15,
    "FINNIFTY": 25,
    "MIDCPNIFTY": 50,
}

# Strike interval for options
STRIKE_INTERVALS = {
    "NIFTY": 50,
    "BANKNIFTY": 100,
    "FINNIFTY": 50,
    "MIDCPNIFTY": 25,
}

# Default equity strike interval
DEFAULT_EQUITY_STRIKE_INTERVAL = 50

# Commodity specs
COMMODITY_SPECS = {
    "GOLD": {"lot_size": 1, "exchange": "MCX", "strike_interval": 100, "unit": "grams"},
    "GOLDM": {"lot_size": 1, "exchange": "MCX", "strike_interval": 100, "unit": "grams"},
    "SILVER": {"lot_size": 1, "exchange": "MCX", "strike_interval": 500, "unit": "kg"},
    "SILVERM": {"lot_size": 1, "exchange": "MCX", "strike_interval": 500, "unit": "kg"},
    "CRUDEOIL": {"lot_size": 1, "exchange": "MCX", "strike_interval": 50, "unit": "barrel"},
    "NATURALGAS": {"lot_size": 1, "exchange": "MCX", "strike_interval": 5, "unit": "mmBtu"},
}


def _get_nearest_expiry():
    """Get the nearest weekly/monthly expiry date (Thursday for NSE)."""
    now = get_ist_now()
    # Find next Thursday
    days_ahead = 3 - now.weekday()  # Thursday = 3
    if days_ahead < 0:
        days_ahead += 7
    if days_ahead == 0 and now.hour >= 15:
        days_ahead = 7
    expiry = (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    return expiry


def _get_monthly_expiry():
    """Get the last Thursday of current month."""
    now = get_ist_now()
    year = now.year
    month = now.month
    # Find last day of month
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    # Find last Thursday
    while last_day.weekday() != 3:
        last_day -= timedelta(days=1)
    expiry = last_day.strftime("%Y-%m-%d")
    if now.date() > last_day.date():
        # Move to next month
        if month == 12:
            last_day = datetime(year + 1, 2, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 2, 1) - timedelta(days=1)
        while last_day.weekday() != 3:
            last_day -= timedelta(days=1)
        expiry = last_day.strftime("%Y-%m-%d")
    return expiry


def _round_to_strike(price, interval):
    """Round price to nearest strike interval."""
    return int(round(price / interval) * interval)


def resolve_contract(symbol, action, current_price, instrument_type="options"):
    """
    Resolve a trading signal into an F&O contract.

    Args:
        symbol: underlying symbol (e.g., "RELIANCE", "NIFTY", "GOLD")
        action: "BUY" or "SELL" — determines CE or PE
        current_price: current market price of the underlying
        instrument_type: "options" (default) or "futures"

    Returns:
        dict with full contract details
    """
    symbol = symbol.upper()

    # Determine option type
    if action == "BUY":
        option_type = "CE"  # Bullish -> Call
    else:
        option_type = "PE"  # Bearish -> Put

    # Determine exchange and lot size
    is_index = symbol in INDEX_LOT_SIZES
    is_commodity = symbol in COMMODITY_SPECS

    if is_commodity:
        spec = COMMODITY_SPECS[symbol]
        exchange = spec["exchange"]
        lot_size = spec["lot_size"]
        strike_interval = spec["strike_interval"]
        expiry = _get_monthly_expiry()
    elif is_index:
        exchange = "NFO"
        lot_size = INDEX_LOT_SIZES[symbol]
        strike_interval = STRIKE_INTERVALS.get(symbol, 50)
        expiry = _get_nearest_expiry()
    else:
        exchange = "NFO"
        lot_size = EQUITY_LOT_SIZES.get(symbol, 500)
        # Equity options strike interval varies by price
        if current_price > 5000:
            strike_interval = 100
        elif current_price > 1000:
            strike_interval = 50
        elif current_price > 500:
            strike_interval = 20
        else:
            strike_interval = 10
        expiry = _get_monthly_expiry()

    # Calculate ATM strike
    atm_strike = _round_to_strike(current_price, strike_interval)

    # For futures
    if instrument_type == "futures":
        trading_symbol = f"{symbol}{expiry.replace('-', '')[2:]}FUT"
        return {
            "symbol": symbol,
            "trading_symbol": trading_symbol,
            "exchange": exchange,
            "lot_size": lot_size,
            "expiry": expiry,
            "instrument_type": "FUT",
            "option_type": None,
            "strike_price": None,
            "current_price": round(current_price, 2),
            "capital_required": round(current_price * lot_size * 0.12, 2),  # ~12% margin
            "action": action,
        }

    # For options
    # OTM by 1 strike for better premium
    if action == "BUY":
        strike = atm_strike + strike_interval  # Slightly OTM CE
    else:
        strike = atm_strike - strike_interval  # Slightly OTM PE

    expiry_code = expiry.replace("-", "")[2:]
    trading_symbol = f"{symbol}{expiry_code}{strike}{option_type}"

    # Estimate option premium (simplified Black-Scholes approximation)
    intrinsic = max(0, current_price - strike) if option_type == "CE" else max(0, strike - current_price)
    time_value = current_price * 0.015  # ~1.5% time value estimate
    estimated_premium = round(max(intrinsic + time_value, current_price * 0.005), 2)

    return {
        "symbol": symbol,
        "trading_symbol": trading_symbol,
        "exchange": exchange,
        "lot_size": lot_size,
        "expiry": expiry,
        "instrument_type": "OPT",
        "option_type": option_type,
        "strike_price": strike,
        "atm_strike": atm_strike,
        "current_price": round(current_price, 2),
        "estimated_premium": estimated_premium,
        "capital_required": round(estimated_premium * lot_size, 2),
        "max_loss": round(estimated_premium * lot_size, 2),  # For option buyers
        "action": f"BUY {option_type}",
        "direction": "BULLISH" if option_type == "CE" else "BEARISH",
    }


def resolve_hedge_contract(portfolio_exposure, nifty_price):
    """
    Resolve a hedge contract based on portfolio exposure.

    Args:
        portfolio_exposure: "HEAVY LONG" or "HEAVY SHORT"
        nifty_price: current NIFTY price

    Returns:
        dict with hedge contract details
    """
    if "LONG" in portfolio_exposure.upper():
        # Hedge longs with NIFTY PUT
        return resolve_contract("NIFTY", "SELL", nifty_price, "options")
    elif "SHORT" in portfolio_exposure.upper():
        # Hedge shorts with NIFTY CALL
        return resolve_contract("NIFTY", "BUY", nifty_price, "options")
    return None
