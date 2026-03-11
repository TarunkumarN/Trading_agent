from kiteconnect import KiteConnect
from config import KITE_API_KEY, KITE_ACCESS_TOKEN

def get_tokens(symbols):
    """Returns dict of {instrument_token: symbol} for KiteStream."""
    kite = KiteConnect(api_key=KITE_API_KEY)
    kite.set_access_token(KITE_ACCESS_TOKEN)
    instruments = kite.instruments("NSE")
    token_map = {i["tradingsymbol"]: i["instrument_token"] for i in instruments}
    result = {}
    for s in symbols:
        sym = s.split(":")[-1]
        if sym in token_map:
            result[token_map[sym]] = sym
        else:
            print(f"[WARNING] Token not found for {sym}")
    return result
