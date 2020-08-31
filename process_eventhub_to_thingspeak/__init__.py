import logging
from json import loads
from os import environ

import azure.functions as func

from .thingspeak import send_message_to_thingspeak

logger = logging.getLogger(f"azure.func.{__name__}")



def main(event: func.EventHubEvent):
    thingspeak_dict = loads(environ.get("thingspeak_keys_dict"))
    thingspeak_api = environ.get("thingspeak_api_endpoint")

    message = loads(event.get_body().decode('utf-8'))
    logger.debug(f"received message: {message}")

    send_message_to_thingspeak(message, thingspeak_dict, thingspeak_api)
    logger.debug("Sent to thingspeak")
