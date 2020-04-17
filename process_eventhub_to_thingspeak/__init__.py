import logging
from os import getenv, environ
from json import loads

import azure.functions as func
logger = logging.getLogger("azure.func")
logger.setLevel(logging.INFO)

from .thingspeak import send_message_to_thingspeak

def getenv_or_exception(var_name: str) -> str:
    """
    fetches an environment variable or raises an exception if not found
    """
    val = getenv(var_name)
    if not val:
        raise Exception(f"can't find envvar {var_name}")
    return val

def main(event: func.EventHubEvent):
    thingspeak_dict = loads(environ["thingspeak_keys_dict"])
    thingspeak_api = environ["thingspeak_api_endpoint"]

    messages = loads(event.get_body().decode('utf-8'))
    for message in messages:
        logger.info(f"received message: {message}")

        send_message_to_thingspeak(message, thingspeak_dict, thingspeak_api)
        logger.info("Sent to thingspeak")