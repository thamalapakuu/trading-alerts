from binance.client import Client


client = Client()


# ==========================
# HOT BUTTON CRYPTO
# ==========================

COMMON_CRYPTO = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",

    # Backend only
    "BNBUSDT"
]


# ==========================
# GET CRYPTO PRICE
# ==========================

def get_crypto_price(symbol):
    symbol = symbol.upper()

    try:
        ticker = client.get_symbol_ticker(symbol=symbol)

        return {
            "symbol": symbol,
            "price": float(ticker["price"])
        }

    except Exception as error:
        print(
            f"Binance price request failed for {symbol}: "
            f"{type(error).__name__}: {error}",
            flush=True
        )

        raise Exception("Crypto price is temporarily unavailable")


# ==========================
# VALIDATE CRYPTO
# ==========================

def validate_crypto(symbol):
    symbol = symbol.upper()

    if symbol in COMMON_CRYPTO:
        return True

    try:
        client.get_symbol_ticker(symbol=symbol)
        return True

    except Exception as error:
        print(
            f"Binance symbol validation failed for {symbol}: "
            f"{type(error).__name__}: {error}",
            flush=True
        )
        return False
