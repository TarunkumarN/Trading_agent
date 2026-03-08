from kiteconnect import KiteConnect
from config import KITE_API_KEY, KITE_ACCESS_TOKEN

def get_tokens(symbols):
    kite = KiteConnect(api_key=KITE_API_KEY)
    kite.set_access_token(KITE_ACCESS_TOKEN)

    instruments = kite.instruments("NSE")

    token_map = {i["tradingsymbol"]: i["instrument_token"] for i in instruments}

    tokens = []

    for s in symbols:
        sym = s.split(":")[1]
        if sym in token_map:
            tokens.append(token_map[sym])

    return tokens
