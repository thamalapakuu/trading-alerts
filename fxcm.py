import os
import time
import threading
from datetime import datetime, timezone

os.environ["LD_LIBRARY_PATH"] = "/app/forexconnect/lib"

from forexconnect import (
    ForexConnect,
    fxcorepy,
)


# ==================================================
# SETTINGS
# ==================================================

# If a quote has not changed for this many seconds
# during an active FX trading period, consider the
# price feed stale.
STALE_PRICE_SECONDS = 180

# Prevent continuous reconnect attempts.
RECONNECT_COOLDOWN_SECONDS = 60


# ==================================================
# COMMON SYMBOLS
# ==================================================

COMMON_FOREX = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "USDCHF",
    "USDCAD",
    "AUDUSD",
    "NZDUSD",

    "EURGBP",
    "EURJPY",
    "EURCHF",
    "EURAUD",

    "GBPJPY",
    "GBPCHF",
    "GBPAUD",

    "AUDJPY",
    "CADJPY",
    "CHFJPY",
    "NZDJPY",

    "AUDCAD",
    "AUDNZD",
    "EURNZD",
    "GBPCAD",
]


COMMON_COMMODITIES = [
    "XAUUSD",
    "XAGUSD",
    "USOIL",
    "COPPER",
]


# ==================================================
# SYMBOL MAPPING
# ==================================================

FXCM_SYMBOL_MAP = {
    "US100": "NAS100",
}


# ==================================================
# GLOBAL FXCM STATE
# ==================================================

fx_connection = None

fx_session_status = None

connection_lock = threading.RLock()

last_reconnect_attempt = 0.0


# Stores the last price we observed for every symbol.
#
# Example:
#
# {
#     "GBPUSD": {
#         "bid": 1.33180,
#         "ask": 1.33193,
#         "changed_at": 123456.78
#     }
# }
#
last_quotes = {}


# ==================================================
# NORMALIZE SYMBOL
# ==================================================

def normalize_symbol(symbol):

    symbol = (
        symbol
        .upper()
        .replace("/", "")
        .replace(" ", "")
    )

    return FXCM_SYMBOL_MAP.get(
        symbol,
        symbol,
    )


# ==================================================
# MARKET TIME CHECK
# ==================================================

def forex_market_should_be_active():
    """
    Conservative check used only for stale-price detection.

    We deliberately avoid considering Saturday/Sunday
    daytime quotes stale because FX markets are normally
    closed then.

    Monday-Friday are treated as active.

    Late Friday UTC is excluded to reduce unnecessary
    reconnect attempts after the weekly close.

    Sunday night UTC is allowed for the weekly reopen.
    """

    now = datetime.now(timezone.utc)

    weekday = now.weekday()
    hour = now.hour

    # Monday = 0
    # Tuesday = 1
    # Wednesday = 2
    # Thursday = 3
    # Friday = 4
    # Saturday = 5
    # Sunday = 6

    if weekday in (0, 1, 2, 3):
        return True

    if weekday == 4:
        # Conservative Friday cutoff.
        return hour < 22

    if weekday == 6:
        # Conservative Sunday reopen.
        return hour >= 22

    return False


# ==================================================
# SESSION STATUS TEXT
# ==================================================

def session_status_name(status):

    try:
        return str(status)
    except Exception:
        return "UNKNOWN"


# ==================================================
# SESSION STATUS CALLBACK
# ==================================================

def on_session_status_changed(session, status):

    global fx_session_status
    global fx_connection

    fx_session_status = status

    print(
        f"🔌 FXCM session status: "
        f"{session_status_name(status)}",
        flush=True,
    )

    # Do not perform another login directly inside this
    # callback. ForexConnect itself may be transitioning.
    #
    # get_price() will reconnect when necessary.


# ==================================================
# CHECK WHETHER SESSION REPORTS CONNECTED
# ==================================================

def session_is_connected():

    global fx_connection
    global fx_session_status

    if fx_connection is None:
        return False

    try:

        status = fx_connection.session.session_status

        return (
            status
            == fxcorepy.AO2GSessionStatus
            .O2GSessionStatus
            .CONNECTED
        )

    except Exception:

        # If this ForexConnect build behaves differently,
        # fall back to the status reported by callback.

        try:

            return (
                fx_session_status
                == fxcorepy.AO2GSessionStatus
                .O2GSessionStatus
                .CONNECTED
            )

        except Exception:

            return False


# ==================================================
# CLOSE CONNECTION
# ==================================================

def close_fxcm():

    global fx_connection
    global fx_session_status

    with connection_lock:

        old_connection = fx_connection

        fx_connection = None
        fx_session_status = None

        if old_connection is None:
            return

        try:

            old_connection.set_session_status_listener(
                None
            )

        except Exception:
            pass

        try:

            old_connection.logout()

        except Exception as e:

            print(
                f"FXCM logout warning: {e}",
                flush=True,
            )

        print(
            "🔌 FXCM disconnected",
            flush=True,
        )


# ==================================================
# INITIALIZE FXCM
# ==================================================

def init_fxcm(force=False):

    global fx_connection
    global fx_session_status

    with connection_lock:

        if (
            not force
            and fx_connection is not None
            and session_is_connected()
        ):

            print(
                "FXCM already connected",
                flush=True,
            )

            return fx_connection


        # ------------------------------------------
        # Clean old connection first
        # ------------------------------------------

        if fx_connection is not None:

            old_connection = fx_connection

            fx_connection = None

            try:
                old_connection.set_session_status_listener(
                    None
                )
            except Exception:
                pass

            try:
                old_connection.logout()
            except Exception:
                pass


        # ------------------------------------------
        # Environment variables
        # ------------------------------------------

        username = os.getenv("FXCM_USERNAME")
        password = os.getenv("FXCM_PASSWORD")
        url = os.getenv("FXCM_URL")

        if not username:
            raise Exception(
                "FXCM_USERNAME missing"
            )

        if not password:
            raise Exception(
                "FXCM_PASSWORD missing"
            )

        if not url:
            raise Exception(
                "FXCM_URL missing"
            )


        print(
            "🔄 Connecting FXCM...",
            flush=True,
        )


        # ------------------------------------------
        # Create new ForexConnect session
        # ------------------------------------------

        fx = ForexConnect()


        # ------------------------------------------
        # Register session-status listener
        # ------------------------------------------

        try:

            fx.set_session_status_listener(
                on_session_status_changed
            )

        except Exception as e:

            print(
                "⚠️ Could not install FXCM "
                f"session listener: {e}",
                flush=True,
            )


        # ------------------------------------------
        # Login
        # ------------------------------------------

        try:

            fx.login(
                username,
                password,
                url,
                "Demo",
            )

        except Exception:

            try:
                fx.logout()
            except Exception:
                pass

            raise


        fx_connection = fx


        try:

            fx_session_status = (
                fx.session.session_status
            )

        except Exception:

            fx_session_status = None


        print(
            "✅ FXCM Connected",
            flush=True,
        )


        return fx_connection


# ==================================================
# GET CONNECTION
# ==================================================

def get_connection():

    global fx_connection

    if fx_connection is None:

        return init_fxcm()


    if not session_is_connected():

        print(
            "⚠️ FXCM session is not connected",
            flush=True,
        )

        return reconnect_fxcm(
            reason="session not connected"
        )


    return fx_connection


# ==================================================
# RECONNECT FXCM
# ==================================================

def reconnect_fxcm(reason="unknown"):

    global last_reconnect_attempt

    with connection_lock:

        now = time.monotonic()

        elapsed = (
            now - last_reconnect_attempt
        )


        # ------------------------------------------
        # Reconnect cooldown
        # ------------------------------------------

        if (
            last_reconnect_attempt > 0
            and elapsed < RECONNECT_COOLDOWN_SECONDS
            and fx_connection is not None
        ):

            print(
                "⏳ FXCM reconnect cooldown active "
                f"({reason})",
                flush=True,
            )

            return fx_connection


        last_reconnect_attempt = now


        print(
            f"🔄 Reconnecting FXCM: {reason}",
            flush=True,
        )


        # ------------------------------------------
        # Destroy existing connection
        # ------------------------------------------

        old_connection = fx_connection

        globals()["fx_connection"] = None

        if old_connection is not None:

            try:

                old_connection.set_session_status_listener(
                    None
                )

            except Exception:
                pass

            try:

                old_connection.logout()

            except Exception:
                pass


        # Give native ForexConnect a very small amount
        # of time to release the old session.
        time.sleep(1)


        # ------------------------------------------
        # New login
        # ------------------------------------------

        new_connection = init_fxcm(
            force=True
        )


        # After reconnect the previous quote-age
        # measurements are no longer useful.
        last_quotes.clear()


        print(
            "✅ FXCM reconnect completed",
            flush=True,
        )


        return new_connection


# ==================================================
# READ OFFER
# ==================================================

def _read_offer(fx, symbol):

    offers = fx.get_table(
        fxcorepy.O2GTableType.OFFERS
    )


    for row in offers:

        fx_symbol = (
            row.instrument
            .replace("/", "")
            .replace(" ", "")
            .upper()
        )


        if fx_symbol == symbol:

            bid = float(row.bid)
            ask = float(row.ask)

            return {
                "symbol": row.instrument,
                "bid": bid,
                "ask": ask,
            }


    return None


# ==================================================
# UPDATE QUOTE HEALTH
# ==================================================

def _update_quote_health(symbol, bid, ask):

    now = time.monotonic()

    previous = last_quotes.get(
        symbol
    )


    # ------------------------------------------
    # First observation
    # ------------------------------------------

    if previous is None:

        last_quotes[symbol] = {
            "bid": bid,
            "ask": ask,
            "changed_at": now,
        }

        return {
            "changed": True,
            "age": 0.0,
            "stale": False,
        }


    # ------------------------------------------
    # Price changed
    # ------------------------------------------

    if (
        previous["bid"] != bid
        or previous["ask"] != ask
    ):

        previous["bid"] = bid
        previous["ask"] = ask
        previous["changed_at"] = now

        return {
            "changed": True,
            "age": 0.0,
            "stale": False,
        }


    # ------------------------------------------
    # Price unchanged
    # ------------------------------------------

    age = (
        now
        - previous["changed_at"]
    )


    stale = (
        forex_market_should_be_active()
        and age >= STALE_PRICE_SECONDS
    )


    return {
        "changed": False,
        "age": age,
        "stale": stale,
    }


# ==================================================
# GET PRICE
# ==================================================

def get_price(symbol):

    global fx_connection

    original_symbol = symbol

    symbol = normalize_symbol(
        symbol
    )


    # We allow one reconnect/retry.
    for attempt in range(2):

        try:

            fx = get_connection()


            # --------------------------------------
            # Read current offer
            # --------------------------------------

            data = _read_offer(
                fx,
                symbol,
            )


            if data is None:

                raise LookupError(
                    f"{original_symbol} not found"
                )


            bid = data["bid"]
            ask = data["ask"]


            # --------------------------------------
            # Sanity check
            # --------------------------------------

            if bid <= 0 or ask <= 0:

                raise Exception(
                    f"Invalid FXCM quote for "
                    f"{original_symbol}: "
                    f"bid={bid}, ask={ask}"
                )


            if ask < bid:

                raise Exception(
                    f"Invalid FXCM spread for "
                    f"{original_symbol}: "
                    f"bid={bid}, ask={ask}"
                )


            # --------------------------------------
            # Quote freshness
            # --------------------------------------

            health = _update_quote_health(
                symbol,
                bid,
                ask,
            )


            # --------------------------------------
            # Stale quote
            # --------------------------------------

            if health["stale"]:

                age = int(
                    health["age"]
                )

                print(
                    f"⚠️ STALE FXCM PRICE | "
                    f"{original_symbol} | "
                    f"Bid: {bid} | "
                    f"Ask: {ask} | "
                    f"Unchanged: {age}s",
                    flush=True,
                )


                if attempt == 0:

                    reconnect_fxcm(
                        reason=(
                            f"{original_symbol} "
                            f"quote unchanged "
                            f"for {age}s"
                        )
                    )

                    continue


                # Most important safety feature:
                # do NOT return a stale quote to
                # the alert monitor.

                raise Exception(
                    f"FXCM stale price for "
                    f"{original_symbol}"
                )


            # --------------------------------------
            # Good quote
            # --------------------------------------

            return {
                "symbol": data["symbol"],
                "bid": bid,
                "ask": ask,
                "quote_age": round(
                    health["age"],
                    1,
                ),
                "quote_changed": health[
                    "changed"
                ],
                "stale": False,
            }


        # ------------------------------------------
        # Invalid symbol
        # ------------------------------------------

        except LookupError:

            raise Exception(
                f"{original_symbol} not found"
            )


        # ------------------------------------------
        # Connection / feed error
        # ------------------------------------------

        except Exception as e:

            print(
                f"FXCM price error "
                f"({original_symbol}): {e}",
                flush=True,
            )


            if attempt == 0:

                try:

                    reconnect_fxcm(
                        reason=(
                            f"price error for "
                            f"{original_symbol}"
                        )
                    )

                    continue

                except Exception as reconnect_error:

                    print(
                        "❌ FXCM reconnect failed: "
                        f"{reconnect_error}",
                        flush=True,
                    )


            raise


    raise Exception(
        f"Unable to get FXCM price for "
        f"{original_symbol}"
    )


# ==================================================
# VALIDATE SYMBOL
# ==================================================

def validate_symbol(symbol):

    symbol = normalize_symbol(
        symbol
    )


    # Common supported list
    if symbol in COMMON_FOREX:
        return True

    if symbol in COMMON_COMMODITIES:
        return True


    try:

        fx = get_connection()

        offers = fx.get_table(
            fxcorepy.O2GTableType.OFFERS
        )


        for row in offers:

            fx_symbol = (
                row.instrument
                .replace("/", "")
                .replace(" ", "")
                .upper()
            )


            if fx_symbol == symbol:
                return True


    except Exception as e:

        print(
            "FXCM validation error:",
            e,
            flush=True,
        )


    return False
