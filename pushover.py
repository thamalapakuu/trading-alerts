import os
import requests


PUSHOVER_APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN")



def send_pushover(user_key, title, message):

    if not PUSHOVER_APP_TOKEN:
        print(
            "❌ PUSHOVER_APP_TOKEN missing",
            flush=True
        )
        return None



    url = "https://api.pushover.net/1/messages.json"



    data = {

        "token": PUSHOVER_APP_TOKEN,

        "user": user_key,

        "title": title,

        "message": message,


        # Emergency notification
        "priority": 2,


        # Minimum allowed by Pushover
        "retry": 30,


        # 10 minutes
        "expire": 600

    }



    try:

        response = requests.post(
            url,
            data=data,
            timeout=15
        )



        print(
            "Pushover Status:",
            response.status_code,
            flush=True
        )



        print(
            "Pushover Response:",
            response.text,
            flush=True
        )



        return response.json()



    except Exception as e:


        print(
            "Pushover Error:",
            e,
            flush=True
        )


        return None





# ==================================
# VALIDATE PUSHOVER USER KEY
# ==================================

def validate_pushover_key(user_key):


    if not PUSHOVER_APP_TOKEN:

        return False



    url = "https://api.pushover.net/1/users/validate.json"



    data = {

        "token": PUSHOVER_APP_TOKEN,

        "user": user_key

    }



    try:

        response = requests.post(

            url,

            data=data,

            timeout=10

        )


        result = response.json()



        print(
            "Pushover Validation:",
            result,
            flush=True
        )


        return result.get("status") == 1



    except Exception as e:


        print(
            "Pushover validation error:",
            e,
            flush=True
        )


        return False




