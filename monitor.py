import asyncio

from fxcm import get_price

from crypto import get_crypto_price

from database import (
    get_active_alerts,
    disable_alert,
    get_pushover_settings,
)

from pushover import send_pushover


telegram_bot = None


# ==================================================
# SETTINGS
# ==================================================

MONITOR_INTERVAL_SECONDS = 10


# ==================================================
# SET TELEGRAM BOT
# ==================================================

def set_bot(bot):

    global telegram_bot

    telegram_bot = bot


# ==================================================
# PRICE FORMATTER
# ==================================================

def format_price(symbol, price):

    symbol = symbol.upper()


    # ----------------------------------------------
    # CRYPTO
    # ----------------------------------------------

    if symbol.endswith("USDT"):

        return f"{price:.2f}"


    # ----------------------------------------------
    # COMMODITIES
    # ----------------------------------------------

    elif symbol in [
        "XAUUSD",
        "XAGUSD",
        "USOIL",
        "COPPER",
    ]:

        return f"{price:.3f}"


    # ----------------------------------------------
    # FOREX / INDICES
    # ----------------------------------------------

    else:

        return f"{price:.5f}"


# ==================================================
# SEND ALERT
# ==================================================

async def send_alert(
    user_id,
    message,
):

    # ----------------------------------------------
    # TELEGRAM
    # ----------------------------------------------

    if telegram_bot:

        try:

            await telegram_bot.send_message(
                chat_id=user_id,
                text=message,
            )

        except Exception as e:

            print(
                f"Telegram send error "
                f"for user {user_id}: {e}",
                flush=True,
            )


    # ----------------------------------------------
    # PUSHOVER
    # ----------------------------------------------

    try:

        pushover_enabled, pushover_key = (
            get_pushover_settings(
                user_id
            )
        )


        if (
            pushover_enabled
            and pushover_key
        ):

            try:

                send_pushover(
                    pushover_key,
                    "🚨 Trading Alert",
                    message,
                )

            except Exception as e:

                print(
                    f"Pushover error: {e}",
                    flush=True,
                )

    except Exception as e:

        print(
            f"Pushover settings error: {e}",
            flush=True,
        )


# ==================================================
# PRICE ROUTER
# ==================================================

def get_current_price(symbol):

    symbol = symbol.upper()


    # ----------------------------------------------
    # CRYPTO
    # ----------------------------------------------

    if symbol.endswith("USDT"):

        data = get_crypto_price(
            symbol
        )

        return round(
            float(data["price"]),
            2,
        )


    # ----------------------------------------------
    # FXCM
    # Forex
    # Commodities
    # Indices
    # ----------------------------------------------

    data = get_price(
        symbol
    )


    return {
        "bid": float(
            data["bid"]
        ),

        "ask": float(
            data["ask"]
        ),

        "quote_age": float(
            data.get(
                "quote_age",
                0,
            )
        ),

        "quote_changed": bool(
            data.get(
                "quote_changed",
                False,
            )
        ),

        "stale": bool(
            data.get(
                "stale",
                False,
            )
        ),
    }


# ==================================================
# LOG CURRENT PRICE
# ==================================================

def log_price(
    symbol,
    current,
):

    if isinstance(
        current,
        dict,
    ):

        age = current.get(
            "quote_age",
            0,
        )

        changed = current.get(
            "quote_changed",
            False,
        )


        status = (
            "NEW"
            if changed
            else f"UNCHANGED {age:.0f}s"
        )


        print(
            f"📡 {symbol} | "
            f"Bid: "
            f"{format_price(symbol, current['bid'])} | "
            f"Ask: "
            f"{format_price(symbol, current['ask'])} | "
            f"{status}",
            flush=True,
        )


    else:

        print(
            f"📡 {symbol} | "
            f"Price: "
            f"{format_price(symbol, current)}",
            flush=True,
        )


# ==================================================
# CHECK ONE ALERT
# ==================================================

async def process_alert(
    alert,
    current,
):

    alert_id = alert[0]
    user_id = alert[1]
    symbol = alert[2]
    target = float(alert[3])
    direction = alert[4]


    # ----------------------------------------------
    # NEVER PROCESS A STALE FXCM QUOTE
    # ----------------------------------------------

    if isinstance(
        current,
        dict,
    ):

        if current.get(
            "stale",
            False,
        ):

            print(
                f"⚠️ Skipping {symbol} alert "
                f"{alert_id}: stale quote",
                flush=True,
            )

            return


    hit = False


    # ==================================================
    # FXCM
    # ==================================================

    if isinstance(
        current,
        dict,
    ):

        bid = current["bid"]
        ask = current["ask"]


        # ------------------------------------------
        # ABOVE
        #
        # Price moving upward.
        # Ask must reach/exceed target.
        # ------------------------------------------

        if direction == "ABOVE":

            if ask >= target:

                hit = True


        # ------------------------------------------
        # BELOW
        #
        # Price moving downward.
        # Bid must reach/fall below target.
        # ------------------------------------------

        elif direction == "BELOW":

            if bid <= target:

                hit = True


    # ==================================================
    # CRYPTO
    # ==================================================

    else:

        if direction == "ABOVE":

            if current >= target:

                hit = True


        elif direction == "BELOW":

            if current <= target:

                hit = True


    # ==================================================
    # NOT HIT
    # ==================================================

    if not hit:
        return


    # ==================================================
    # PRICE USED FOR ALERT MESSAGE
    # ==================================================

    if isinstance(
        current,
        dict,
    ):

        if direction == "BELOW":

            alert_price = current[
                "bid"
            ]

        else:

            alert_price = current[
                "ask"
            ]

    else:

        alert_price = current


    # ==================================================
    # SEND ALERT
    # ==================================================

    message = (
        "🚨 PRICE ALERT HIT\n\n"

        f"📊 Symbol:\n"
        f"{symbol}\n\n"

        f"📍 Direction:\n"
        f"{direction}\n\n"

        f"🎯 Target:\n"
        f"{format_price(symbol, target)}\n\n"

        f"💰 Current Price:\n"
        f"{format_price(symbol, alert_price)}\n\n"

        "✅ Alert Completed"
    )


    await send_alert(
        user_id,
        message,
    )


    # Only disable AFTER attempting notification.
    disable_alert(
        alert_id
    )


    print(
        f"🚨 ALERT HIT | "
        f"ID: {alert_id} | "
        f"{symbol} | "
        f"Target: "
        f"{format_price(symbol, target)} | "
        f"Price: "
        f"{format_price(symbol, alert_price)}",
        flush=True,
    )


# ==================================================
# CHECK ALERTS
# ==================================================

async def check_alerts():

    alerts = get_active_alerts()


    if not alerts:

        return


    # ==================================================
    # PRICE CACHE
    #
    # This is recreated on EVERY monitoring cycle.
    #
    # It means:
    #
    # GBPUSD alert #1
    # GBPUSD alert #2
    # GBPUSD alert #3
    #
    # all use ONE GBPUSD price fetch for this cycle.
    # ==================================================

    price_cache = {}

    failed_symbols = set()


    # ==================================================
    # FETCH EACH SYMBOL ONCE
    # ==================================================

    for alert in alerts:

        symbol = (
            alert[2]
            .upper()
        )


        # Already fetched this cycle.
        if symbol in price_cache:
            continue


        # Already failed this cycle.
        if symbol in failed_symbols:
            continue


        try:

            current = get_current_price(
                symbol
            )


            price_cache[
                symbol
            ] = current


            log_price(
                symbol,
                current,
            )


        except Exception as e:

            failed_symbols.add(
                symbol
            )


            print(
                f"❌ PRICE ERROR | "
                f"{symbol} | {e}",
                flush=True,
            )


    # ==================================================
    # PROCESS ALL ALERTS USING CACHED PRICES
    # ==================================================

    for alert in alerts:

        alert_id = alert[0]
        symbol = (
            alert[2]
            .upper()
        )


        if symbol not in price_cache:

            print(
                f"⚠️ Alert {alert_id} skipped | "
                f"{symbol} price unavailable",
                flush=True,
            )

            continue


        current = price_cache[
            symbol
        ]


        try:

            await process_alert(
                alert,
                current,
            )


        except Exception as e:

            print(
                f"Monitor error | "
                f"Alert ID: {alert_id} | "
                f"{symbol} | {e}",
                flush=True,
            )


# ==================================================
# MAIN MONITOR LOOP
# ==================================================

async def monitor_loop():

    print(
        "📡 Monitor running",
        flush=True,
    )


    while True:

        cycle_started = (
            asyncio.get_running_loop()
            .time()
        )


        try:

            await check_alerts()


        except asyncio.CancelledError:

            print(
                "📡 Monitor stopped",
                flush=True,
            )

            raise


        except Exception as e:

            print(
                "Monitor loop error:",
                e,
                flush=True,
            )


        # ------------------------------------------
        # Maintain approximately one check every
        # MONITOR_INTERVAL_SECONDS.
        # ------------------------------------------

        elapsed = (
            asyncio.get_running_loop()
            .time()
            - cycle_started
        )


        sleep_time = max(
            1,
            MONITOR_INTERVAL_SECONDS
            - elapsed,
        )


        await asyncio.sleep(
            sleep_time
        )
