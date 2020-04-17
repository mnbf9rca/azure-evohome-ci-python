import logging
from os import getenv, environ

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
    message = event.get_body().decode('utf-8')
    logger.info(f"received message: {message}")
    thingspeak_dict = environ["thingspeak_keys_dict"]
    thingspeak_api = environ["thingspeak_api_endpoint"]
    send_message_to_thingspeak(message, thingspeak_dict, thingspeak_api)
    logger.info("Sent to thingspeak")