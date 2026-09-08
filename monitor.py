import asyncio


from fxcm import get_price

from crypto import get_crypto_price


from database import (
    get_active_alerts,
    disable_alert,
    get_pushover_settings
)

from pushover import send_pushover



telegram_bot = None





# ==========================
# SET TELEGRAM BOT
# ==========================


def set_bot(bot):

    global telegram_bot

    telegram_bot = bot







# ==========================
# PRICE FORMATTER
# ==========================


def format_price(symbol, price):

    symbol = symbol.upper()


    # ======================
    # CRYPTO
    # ======================

    if symbol.endswith("USDT"):

        return f"{price:.2f}"



    # ======================
    # COMMODITIES
    # ======================

    elif symbol in [

        "XAUUSD",
        "XAGUSD",
        "USOIL",
        "COPPER"

    ]:

        return f"{price:.3f}"



    # ======================
    # FOREX
    # ======================

    else:

        return f"{price:.5f}"









# ==========================
# SEND ALERT
# ==========================


async def send_alert(user_id, message):


    # ==========================
    # TELEGRAM
    # ==========================

    if telegram_bot:

        await telegram_bot.send_message(
            chat_id=user_id,
            text=message
        )


    # ==========================
    # PUSHOVER
    # ==========================

    pushover_enabled, pushover_key = get_pushover_settings(user_id)


    if pushover_enabled and pushover_key:

        try:

            send_pushover(
                pushover_key,
                "🚨 Trading Alert",
                message
            )


        except Exception as e:

            print(
                f"Pushover error: {e}",
                flush=True
            )



# ==========================
# PRICE ROUTER
# ==========================


def get_current_price(symbol):


    symbol = symbol.upper()



    # ======================
    # CRYPTO
    # ======================


    if symbol.endswith("USDT"):


        data = get_crypto_price(symbol)


        return round(

            float(data["price"]),

            2

        )





    # ======================
    # FXCM
    # Forex
    # Commodities
    # Indices
    # ======================


    else:


        data = get_price(symbol)


        return {

            "bid": float(data["bid"]),

            "ask": float(data["ask"])

        }









# ==========================
# CHECK ALERTS
# ==========================


async def check_alerts():


    alerts = get_active_alerts()



    for alert in alerts:



        alert_id = alert[0]

        user_id = alert[1]

        symbol = alert[2]

        target = float(alert[3])

        direction = alert[4]





        try:



            current = get_current_price(symbol)






            # ======================
            # LIVE LOG
            # ======================


            if isinstance(current, dict):


                print(

                    f"{symbol} | "
                    f"Bid: {format_price(symbol,current['bid'])} | "
                    f"Ask: {format_price(symbol,current['ask'])} | "
                    f"Target: {format_price(symbol,target)} | "
                    f"Direction: {direction}",

                    flush=True

                )



            else:


                print(

                    f"{symbol} | "
                    f"Price: {format_price(symbol,current)} | "
                    f"Target: {format_price(symbol,target)} | "
                    f"Direction: {direction}",

                    flush=True

                )








            # ======================
            # TARGET CHECK
            # ======================


            hit = False






            # ======================
            # FXCM
            # ======================


            if isinstance(current, dict):


                bid = current["bid"]

                ask = current["ask"]





                # BUY SIDE
                # price going UP

                if direction == "ABOVE":


                    if ask >= target:


                        hit = True






                # SELL SIDE
                # price going DOWN

                elif direction == "BELOW":


                    if bid <= target:


                        hit = True








            # ======================
            # CRYPTO
            # ======================


            else:


                if direction == "ABOVE":


                    if current >= target:


                        hit = True





                elif direction == "BELOW":


                    if current <= target:


                        hit = True









            # ======================
            # SEND ALERT
            # ======================


            if hit:



                if isinstance(current, dict):

                    if direction == "BELOW":
                        alert_price = current["bid"]

                    else:
                        alert_price = current["ask"]

                else:
                    alert_price = current





                await send_alert(


                    user_id,


                    f"""
🚨 PRICE ALERT HIT


📊 Symbol:
{symbol}


📍 Direction:
{direction}


🎯 Target:
{format_price(symbol,target)}


💰 Current Price:
{format_price(symbol,alert_price)}


✅ Alert Completed
"""

                )





                disable_alert(alert_id)









        except Exception as e:



            print(

                f"Monitor error for {symbol}: {e}",

                flush=True

            )









# ==========================
# MAIN MONITOR LOOP
# ==========================


async def monitor_loop():


    print(

        "📡 Monitor running",

        flush=True

    )



    while True:



        try:


            await check_alerts()



        except Exception as e:


            print(

                "Monitor loop error:",

                e,

                flush=True

            )





        await asyncio.sleep(10)
