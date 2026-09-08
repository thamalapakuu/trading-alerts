import os

os.environ["LD_LIBRARY_PATH"] = "/app/forexconnect/lib"


from forexconnect import (
    ForexConnect,
    fxcorepy
)


# ==========================
# COMMON SYMBOLS
# ==========================

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
    "GBPCAD"

]


COMMON_COMMODITIES = [

    "XAUUSD",
    "XAGUSD",
    "USOIL",
    "COPPER"

]


# ==========================
# SYMBOL MAPPING
# ==========================

FXCM_SYMBOL_MAP = {

    "US100": "NAS100"

}


# ==========================
# GLOBAL CONNECTION
# ==========================

fx_connection = None



# ==========================
# INITIALIZE FXCM
# ==========================

def init_fxcm():

    global fx_connection


    if fx_connection:

        print(
            "FXCM already connected",
            flush=True
        )

        return



    print(
        "Connecting FXCM...",
        flush=True
    )


    fx = ForexConnect()



    fx.login(

        os.getenv("FXCM_USERNAME"),

        os.getenv("FXCM_PASSWORD"),

        os.getenv("FXCM_URL"),

        "Demo"

    )



    fx_connection = fx


    print(
        "✅ FXCM Connected",
        flush=True
    )




# ==========================
# GET CONNECTION
# ==========================

def get_connection():

    global fx_connection


    if fx_connection is None:

        init_fxcm()


    return fx_connection




# ==========================
# NORMALIZE SYMBOL
# ==========================

def normalize_symbol(symbol):

    symbol = (

        symbol

        .upper()

        .replace("/", "")

    )


    return FXCM_SYMBOL_MAP.get(

        symbol,

        symbol

    )




# ==========================
# GET PRICE
# ==========================

def get_price(symbol):


    global fx_connection


    original_symbol = symbol


    symbol = normalize_symbol(symbol)



    try:


        fx = get_connection()



        offers = fx.get_table(

            fxcorepy.O2GTableType.OFFERS

        )



        for row in offers:



            fx_symbol = (

                row.instrument

                .replace("/", "")

                .upper()

            )



            if fx_symbol == symbol:



                return {

                    "symbol": row.instrument,

                    "bid": row.bid,

                    "ask": row.ask

                }




        # ==========================
        # SYMBOL DOES NOT EXIST
        # ==========================

        raise Exception(

            f"{original_symbol} not found"

        )





    except Exception as e:



        print(

            "FXCM price error:",

            e,

            flush=True

        )



        error_text = str(e)



        # ==========================
        # INVALID SYMBOL
        # NO RECONNECT
        # ==========================

        if "not found" in error_text:


            raise Exception(

                error_text

            )



        # ==========================
        # CONNECTION ERROR
        # RECONNECT ONCE
        # ==========================


        fx_connection = None


        init_fxcm()



        fx = get_connection()



        offers = fx.get_table(

            fxcorepy.O2GTableType.OFFERS

        )



        for row in offers:



            fx_symbol = (

                row.instrument

                .replace("/", "")

                .upper()

            )



            if fx_symbol == symbol:



                return {

                    "symbol": row.instrument,

                    "bid": row.bid,

                    "ask": row.ask

                }



        raise Exception(

            f"{original_symbol} not found"

        )





# ==========================
# VALIDATE SYMBOL
# ==========================

def validate_symbol(symbol):


    symbol = normalize_symbol(symbol)



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

                .upper()

            )



            if fx_symbol == symbol:

                return True



    except Exception as e:


        print(

            "FXCM validation error:",

            e,

            flush=True

        )



    return False




# ==========================
# CLOSE CONNECTION
# ==========================

def close_fxcm():


    global fx_connection



    if fx_connection:


        try:

            fx_connection.logout()


        except:

            pass



        fx_connection = None



        print(

            "FXCM disconnected",

            flush=True

        )
