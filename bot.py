import requests

from datetime import datetime
from zoneinfo import ZoneInfo
import os
import asyncio


from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update
)

from pushover import (
    send_pushover,
    validate_pushover_key
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)



from database import (
    init_db,
    add_alert,
    get_user_alerts,
    remove_multiple_alerts,
    get_pushover_key,
    get_pushover_status,
    disable_pushover,
    enable_pushover,
    save_pushover_key
)



from fxcm import (
    get_price,
    init_fxcm
)



from crypto import (
    get_crypto_price
)



import monitor





BOT_TOKEN = os.getenv("BOT_TOKEN")

async def setpush(update, context):

    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "Send your Pushover User Key.\n\nExample:\n/setpush uQi8xxxxxxxx"
        )
        return

    pushover_key = context.args[0]

    save_pushover_key(
        user_id,
        pushover_key
    )

    enable_pushover(user_id)

    await update.message.reply_text(
        "✅ Pushover notification enabled"
    )



def format_market_price(symbol, price):

    symbol = symbol.upper()


    # Crypto
    if symbol.endswith("USDT"):

        return f"{price:.2f}"


    # Commodities
    if symbol in [
        "XAUUSD",
        "XAGUSD",
        "USOIL",
        "COPPER"
    ]:

        return f"{price:.2f}"


    # Indices
    if symbol in [
        "SPX500",
        "NAS100",
        "US30"
    ]:

        return f"{price:.2f}"


    # Forex
    return f"{price:.5f}"

# ==================================================
# MAIN MENU
# ==================================================


main_menu = [

    ["📈 Add Alert", "📋 My Alerts"],

    ["🗑 Remove Alert","🔔 Notification Settings"],

    ["ℹ️ Status"]

]







# ==================================================
# MARKET MENU
# ==================================================


market_menu = [

    ["💱 Forex", "🪙 Crypto"],

    ["🥇 Commodities", "📊 Indices"],

    ["⬅️ Back"]

]






notification_menu_connected = [

    ["🧪 Test Alert"],

    ["🔄 Change User Key"],

    ["❌ Disable Pushover"],

    ["⬅️ Back"]

]


notification_menu_disabled = [

    ["🔑 Enter Pushover Key"],

    ["⬅️ Back"]

]


# ==================================================
# FOREX MENU
# ==================================================


forex_menu = [

    ["EURUSD", "GBPUSD"],

    ["USDJPY", "GBPJPY"],

    ["✏️ Enter Forex Pair"],

    ["⬅️ Back"]

]








# ==================================================
# CRYPTO MENU
# ==================================================


crypto_menu = [

    ["BTCUSDT", "ETHUSDT"],

    ["SOLUSDT", "XRPUSDT"],

    ["✍️ Enter Crypto Pair"],

    ["⬅️ Back"]

]








# ==================================================
# COMMODITY MENU
# ==================================================


commodity_menu = [

    ["XAUUSD", "XAGUSD"],

    ["USOIL", "COPPER"],

    ["✍️ Enter Commodity"],

    ["⬅️ Back"]

]








# ==================================================
# INDICES MENU
# ==================================================


indices_menu = [

    ["SPX500", "US30"],

    ["✏️ Enter Index"],

    ["⬅️ Back"]

]








# ==================================================
# HOT SYMBOLS
# ==================================================


HOT_SYMBOLS = [

    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "GBPJPY",


    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",


    "XAUUSD",
    "XAGUSD",
    "USOIL",
    "COPPER",


    "SPX500",
    "US30"
    
]








# ==================================================
# START COMMAND
# ==================================================


async def start(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):


    context.user_data.clear()



    await update.message.reply_text(

        "🚀 Universal Trading Alert Platform",

        reply_markup=ReplyKeyboardMarkup(

            main_menu,

            resize_keyboard=True

        )

    )
# ==================================================
# SYSTEM STATUS CHECK
# ==================================================

async def system_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # ==========================
    # BOT STATUS
    # ==========================

    bot_status = "🟢 Bot: Online"



    # ==========================
    # FXCM LIVE CHECK
    # ==========================

    try:

        fxcm_check = get_price("EURUSD")


        if fxcm_check:

            eurusd_price = fxcm_check["bid"]

            fxcm_status = (
                "🟢 FXCM: Connected\n"
                f"💱 EURUSD: {format_market_price('EURUSD', eurusd_price)}"
            )

        else:

            fxcm_status = (
                "🔴 FXCM: Disconnected"
            )


    except Exception:


        fxcm_status = (
            "🔴 FXCM: Disconnected"
        )





    # ==========================
    # BINANCE LIVE CHECK
    # ==========================

    try:
        response = requests.get(
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
            timeout=10
        )

        response.raise_for_status()

        data = response.json()
        btc_price = float(data["price"])

        binance_status = (
            "🟢 Binance: Connected\n"
            f"₿ BTCUSDT: ${btc_price:,.2f}"
        )

    except Exception as error:
        print(
            f"Binance status check failed: "
            f"{type(error).__name__}: {error}",
            flush=True
        )

        binance_status = "🔴 Binance: Disconnected"





    # ==========================
    # TIME (IST)
    # ==========================

    ist_time = datetime.now(
        ZoneInfo("Asia/Kolkata")
    )

    current_time = ist_time.strftime(
        "%d-%m-%Y %H:%M:%S"
    )





    message = f"""
ℹ️ System Status


{bot_status}


{fxcm_status}


{binance_status}


🕒 Last Update:
{current_time}
"""





    await update.message.reply_text(

        message,

        reply_markup=ReplyKeyboardMarkup(

            main_menu,

            resize_keyboard=True

        )

    )
# ==================================================
# MENU HANDLER
# ==================================================


async def menu_handler(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):


    text = update.message.text

    user_id = update.message.from_user.id



    # ==================================================
    # PUSHOVER KEY INPUT
    # ==================================================

    if context.user_data.get("waiting_for_pushover_key"):

        key = text.strip()


        await update.message.reply_text(
            "🔄 Validating Pushover key..."
        )


        valid = validate_pushover_key(key)



        if valid:


            save_pushover_key(
                user_id,
                key
            )


            enable_pushover(
                user_id
            )



            context.user_data.pop(
                "waiting_for_pushover_key",
                None
            )



            await update.message.reply_text(

                "✅ Pushover Connected\n\n"
                "🚨 Emergency alerts enabled",

                reply_markup=ReplyKeyboardMarkup(
                    main_menu,
                    resize_keyboard=True
                )

            )



        else:


            await update.message.reply_text(

                "❌ Invalid Pushover User Key\n\n"
                "Please check your key and try again."

            )


        return






    # ==================================================
    # ADD ALERT
    # ==================================================


    if text == "📈 Add Alert":


        context.user_data.clear()



        await update.message.reply_text(

            "🌍 Select Market",

            reply_markup=ReplyKeyboardMarkup(

                market_menu,

                resize_keyboard=True

            )

        )







    # ==================================================
    # REGULAR BACK BUTTON
    # ==================================================

    elif text == "⬅️ Back":

        market = context.user_data.get("market")
        symbol = context.user_data.get("symbol")
        custom_symbol = context.user_data.get("custom_symbol")

        # From selected symbol / target-price screen
        # Back to the relevant symbol menu
        if symbol or custom_symbol:

            context.user_data.pop("symbol", None)
            context.user_data.pop("custom_symbol", None)

            if market == "forex":

                await update.message.reply_text(

                    "💱 Select Forex Pair",

                    reply_markup=ReplyKeyboardMarkup(
                        forex_menu,
                        resize_keyboard=True
                    )

                )

            elif market == "crypto":

                await update.message.reply_text(

                    "🪙 Select Crypto Pair",

                    reply_markup=ReplyKeyboardMarkup(
                        crypto_menu,
                        resize_keyboard=True
                    )

                )

            elif market == "commodity":

                await update.message.reply_text(

                    "🥇 Select Commodity",

                    reply_markup=ReplyKeyboardMarkup(
                        commodity_menu,
                        resize_keyboard=True
                    )

                )

            elif market == "indices":

                await update.message.reply_text(

                    "📊 Select Index",

                    reply_markup=ReplyKeyboardMarkup(
                        indices_menu,
                        resize_keyboard=True
                    )

                )

            return

        # From a symbol menu
        # Back to Select Market
        elif market:

            context.user_data.clear()

            await update.message.reply_text(

                "🌍 Select Market",

                reply_markup=ReplyKeyboardMarkup(
                    market_menu,
                    resize_keyboard=True
                )

            )

            return

        # From Select Market
        # Back to the main menu
        else:

            context.user_data.clear()

            await update.message.reply_text(

                "🚀 Universal Trading Alert Platform",

                reply_markup=ReplyKeyboardMarkup(
                    main_menu,
                    resize_keyboard=True
                )

            )

            return







    # ==================================================
    # FOREX
    # ==================================================


    elif text == "💱 Forex":


        context.user_data["market"] = "forex"



        await update.message.reply_text(

            "💱 Select Forex Pair",

            reply_markup=ReplyKeyboardMarkup(

                forex_menu,

                resize_keyboard=True

            )

        )








    # ==================================================
    # CRYPTO
    # ==================================================


    elif text == "🪙 Crypto":


        context.user_data["market"] = "crypto"



        await update.message.reply_text(

            "🪙 Select Crypto Pair",

            reply_markup=ReplyKeyboardMarkup(

                crypto_menu,

                resize_keyboard=True

            )

        )








    # ==================================================
    # COMMODITIES
    # ==================================================


    elif text == "🥇 Commodities":


        context.user_data["market"] = "commodity"



        await update.message.reply_text(

            "🥇 Select Commodity",

            reply_markup=ReplyKeyboardMarkup(

                commodity_menu,

                resize_keyboard=True

            )

        )








    # ==================================================
    # INDICES
    # ==================================================


    elif text == "📊 Indices":


        context.user_data["market"] = "indices"



        await update.message.reply_text(

            "📊 Select Index",

            reply_markup=ReplyKeyboardMarkup(

                indices_menu,

                resize_keyboard=True

            )

        )








    # ==================================================
    # SYMBOL SELECTED
    # ==================================================

    elif text in HOT_SYMBOLS:


        context.user_data["symbol"] = text


        price_keyboard = [

            ["⬅️ Back"]

        ]


        # ==========================
        # SHOW CURRENT PRICE
        # ==========================


        if text.endswith("USDT"):


            data = get_crypto_price(text)
            current_price = float(data["price"])


            price_message = (

                f"📊 {text} Selected\n\n"

                f"💰 Current Price:\n"

                f"{format_market_price(text, current_price)}\n\n"
                "Enter target price:"

            )


        else:


            data = get_price(text)


            price_message = (

                f"📊 {text} Selected\n\n"

                f"📈 Current Bid:\n"
                f"{float(data['bid']):.5f}\n\n"

                f"📉 Current Ask:\n"
                f"{float(data['ask']):.5f}\n\n"

                "Enter target price:"

            )



        await update.message.reply_text(

            price_message,

            reply_markup=ReplyKeyboardMarkup(

                price_keyboard,

                resize_keyboard=True

            )

        )








    # ==================================================
    # MANUAL INPUT BUTTONS
    # ==================================================


    elif text in [

        "✏️ Enter Forex Pair",

        "✍️ Enter Crypto Pair",

        "✍️ Enter Commodity",

        "✏️ Enter Index"

    ]:


        context.user_data["custom_symbol"] = True



        market = context.user_data.get(

            "market"

        )



        if market == "crypto":


            await update.message.reply_text(

                "🪙 Enter Crypto Symbol\n\n"
                "Example:\n"
                "BNBUSDT\nDOGEUSDT\nADAUSDT"

            )



        elif market == "commodity":


            await update.message.reply_text(

                "🥇 Enter Commodity Symbol\n\n"
                "Example:\n"
                "NATGAS\nCOFFEE"

            )



        elif market == "indices":


            await update.message.reply_text(

                "📊 Enter Index Symbol\n\n"
                "Example:\n"
                "GER30\nUK100"

            )



        else:


            await update.message.reply_text(

                "💱 Enter Forex Pair\n\n"
                "Example:\n"
                "AUDUSD\nEURJPY"

            )
    # ==================================================
    # CUSTOM SYMBOL INPUT
    # ==================================================

    elif context.user_data.get("custom_symbol"):

        symbol = text.upper().replace("/", "").replace(" ", "")

        try:

            context.user_data["symbol"] = symbol
            context.user_data.pop("custom_symbol", None)

            if symbol.endswith("USDT"):

                data = get_crypto_price(symbol)
                current_price = float(data["price"])

                price_message = (
                    f"📊 {symbol} Selected\n\n"
                    f"💰 Current Price:\n"
                    f"{format_market_price(symbol, current_price)}\n\n"
                    "Enter target price:"
                )

            else:

                data = get_price(symbol)

                bid = float(data["bid"])
                ask = float(data["ask"])

                price_message = (
                    f"📊 {symbol} Selected\n\n"
                    f"📈 Current Bid:\n"
                    f"{format_market_price(symbol, bid)}\n\n"
                    f"📉 Current Ask:\n"
                    f"{format_market_price(symbol, ask)}\n\n"
                    "Enter target price:"
                )

            await update.message.reply_text(
                price_message,
                reply_markup=ReplyKeyboardMarkup(
                    [["⬅️ Back"]],
                    resize_keyboard=True
                )
            )

        except Exception:

            context.user_data.pop("symbol", None)

            await update.message.reply_text(
                f"❌ Symbol not available: {symbol}\n\n"
                "Please check the symbol and try again."
            )
            
# ==================================================
# MY ALERTS
# ==================================================


    elif text == "📋 My Alerts":


        alerts = get_user_alerts(user_id)



        if not alerts:


            await update.message.reply_text(

                "📋 No active alerts."

            )

            return






        msg = (

            "📋 Your Active Alerts:\n\n"

        )



        for alert in alerts:


            msg += (

                f"🆔 ID: {alert[0]}\n"
                f"📊 Symbol: {alert[2]}\n"
                f"🎯 Target: {alert[3]}\n"
                f"📈 Direction: {alert[4]}\n\n"

            )





        await update.message.reply_text(

            msg

        )









# ==================================================
# REMOVE ALERT
# ==================================================


    elif text == "🗑 Remove Alert":


        alerts = get_user_alerts(user_id)



        if not alerts:


            await update.message.reply_text(

                "📋 No active alerts."

            )

            return





        buttons = []



        for alert in alerts:


            buttons.append(

                [

                    InlineKeyboardButton(

                        f"{alert[2]} | {alert[3]}",

                        callback_data=f"toggle_{alert[0]}"

                    )

                ]

            )




        buttons.append(

            [

                InlineKeyboardButton(

                    "🗑 Delete Selected",

                    callback_data="delete_selected"

                )

            ]

        )



        context.user_data["delete_list"] = []




        await update.message.reply_text(

            "🗑 Select alerts to remove:\n\n"
            "Tap alerts to select\n"
            "Then press Delete Selected",

            reply_markup=InlineKeyboardMarkup(

                buttons

            )

        )





    # ==================================================
    # NOTIFICATION SETTINGS
    # ==================================================

    elif text == "🔔 Notification Settings":

        status = get_pushover_status(user_id)


        if status == 1:

            message = """
🔔 Notification Settings


Pushover:
✅ Connected


Emergency Alerts:
🚨 Enabled


Choose an option:
"""


            keyboard = notification_menu_connected


        else:

            message = """
🔔 Notification Settings


Pushover:
❌ Not Connected


Emergency Alerts:
OFF


Choose an option:
"""


            keyboard = notification_menu_disabled



        await update.message.reply_text(

            message,

            reply_markup=ReplyKeyboardMarkup(

                keyboard,

                resize_keyboard=True

            )

        )

# ==================================================
# NOTIFICATION MENU ACTIONS
# ==================================================

    elif text == "🧪 Test Alert":

        key = get_pushover_key(user_id)

        if not key:

            await update.message.reply_text(
                "❌ Pushover is not connected.\nPlease enter your Pushover Key from Notification Settings."
            )
            return


        from pushover import send_pushover


        send_pushover(
            key,
            "🧪 Test Alert",
            "✅ Your Trading Alert notifications are working!"
        )


        await update.message.reply_text(
            "✅ Test notification sent"
        )



    elif text == "❌ Disable Pushover":

        disable_pushover(user_id)


        await update.message.reply_text(

            "🔴 Pushover Disabled",

            reply_markup=ReplyKeyboardMarkup(
                main_menu,
                resize_keyboard=True
            )

        )



    elif text in [
           "🔑 Enter Pushover Key",
           "🔄 Change User Key"
    ]:

           context.user_data["waiting_for_pushover_key"] = True


           await update.message.reply_text(

              "🔑 Enter your Pushover User Key:\n\n"
              "Paste the key here."

         )





# ==================================================
# STATUS BUTTON
# ==================================================


    elif text == "ℹ️ Status":

            await system_status(
                update,
                context
            )








# ==================================================
# REMOVE UNUSED BUTTON
# ==================================================



# ==================================================
# INLINE CALLBACK HANDLER
# ==================================================


async def delete_callback(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):


    query = update.callback_query


    await query.answer()



    data = query.data





    # ======================================
    # SELECT / UNSELECT ALERT
    # ======================================


    if data.startswith("toggle_"):



        alert_id = int(

            data.split("_")[1]

        )



        selected = context.user_data.get(

            "delete_list",

            []

        )





        if alert_id in selected:


            selected.remove(alert_id)



        else:


            selected.append(alert_id)





        context.user_data["delete_list"] = selected





        alerts = get_user_alerts(

            query.from_user.id

        )



        buttons = []





        for alert in alerts:



            mark = "✅ " if alert[0] in selected else ""



            buttons.append(

                [

                    InlineKeyboardButton(

                        f"{mark}{alert[2]} | {alert[3]}",

                        callback_data=f"toggle_{alert[0]}"

                    )

                ]

            )







        buttons.append(

            [

                InlineKeyboardButton(

                    "🗑 Delete Selected",

                    callback_data="delete_selected"

                )

            ]

        )






        await query.edit_message_reply_markup(

            reply_markup=InlineKeyboardMarkup(

                buttons

            )

        )







    # ======================================
    # DELETE SELECTED
    # ======================================


    elif data == "delete_selected":



        selected = context.user_data.get(

            "delete_list",

            []

        )





        if not selected:



            await query.answer(

                "Select alerts first",

                show_alert=True

            )

            return







        remove_multiple_alerts(

            selected

        )





        context.user_data.clear()






        await query.edit_message_text(

            "✅ Selected alerts removed."

        )

# ==================================================
# SAVE ALERT
# ==================================================


async def save_alert(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):


    user_id = update.message.from_user.id


    try:


        target = float(

            update.message.text

        )



        symbol = context.user_data.get(

            "symbol"

        )



        if not symbol:


            return






        # ==========================
        # GET CURRENT PRICE
        # ==========================


        if symbol.endswith("USDT"):


            data = get_crypto_price(symbol)


            current_price = float(

                data["price"]

            )


        else:


            data = get_price(symbol)


            bid = float(data["bid"])
            ask = float(data["ask"])

            current_price = (bid + ask) / 2

        








        # ==========================
        # DETERMINE DIRECTION
        # ==========================


        if current_price >= target:


            direction = "BELOW"



        else:


            direction = "ABOVE"








        add_alert(

            user_id,

            symbol,

            target,

            direction

        )








        await update.message.reply_text(


            "✅ Alert Saved\n\n"

            f"📊 Symbol: {symbol}\n"

            f"💵 Current: {format_market_price(symbol, current_price)}\n"

            f"🎯 Target: {format_market_price(symbol, target)}\n"

            f"📈 Direction: {direction}\n\n"

            "🚀 Monitoring Started",


            reply_markup=ReplyKeyboardMarkup(

                main_menu,

                resize_keyboard=True

            )


        )







        context.user_data.clear()






    except Exception as e:



        await update.message.reply_text(

            f"❌ Error creating alert\n\n{e}"

        )








# ==================================================
# MONITOR START
# ==================================================


async def start_monitor(app):


    print(

        "📡 Starting monitor...",

        flush=True

    )



    monitor.set_bot(

        app.bot

    )



    asyncio.create_task(

        monitor.monitor_loop()

    )








# ==================================================
# MAIN
# ==================================================


def main():



    print(

        "STEP 1",

        flush=True

    )



    if not BOT_TOKEN:


        raise Exception(

            "BOT_TOKEN missing"

        )






    print(

        "STEP 2",

        flush=True

    )



    init_db()



    print(

        "Connecting FXCM...",

        flush=True

    )



    init_fxcm()






    print(

        "STEP 3",

        flush=True

    )





    app = (

        Application

        .builder()

        .token(BOT_TOKEN)

        .post_init(start_monitor)

        .build()

    )






    print(

        "STEP 4",

        flush=True

    )






    # ==========================
    # COMMAND
    # ==========================


    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )
    app.add_handler(
        CommandHandler(
            "setpush",
            setpush
        )
    )








    # ==========================
    # INLINE BUTTONS
    # ==========================


    app.add_handler(

        CallbackQueryHandler(

            delete_callback

        )

    )







    # ==========================
    # PRICE INPUT
    # MUST BE ABOVE MENU
    # ==========================


    app.add_handler(

        MessageHandler(

            filters.Regex(

                r"^\d+(\.\d+)?$"

            ),

            save_alert

        )

    )








    # ==========================
    # NORMAL BUTTONS
    # ==========================


    app.add_handler(

        MessageHandler(

            filters.TEXT & ~filters.COMMAND,

            menu_handler

        )

    )







    print(

        "🚀 Bot Started",

        flush=True

    )





    app.run_polling(

        drop_pending_updates=False,

        allowed_updates=Update.ALL_TYPES

    )







# ==================================================
# RUN
# ==================================================


if __name__ == "__main__":


    main()
