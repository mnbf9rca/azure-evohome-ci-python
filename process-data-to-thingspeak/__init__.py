import logging
from os import getenv
from json import loads, dumps

import azure.functions as func
import requests

logger = logging.getLogger("azure.eventhub")
logger.addFilter(logging.Filter(__name__))


def getenv_or_exception(var_name: str) -> str:
    """
    fetches an environment variable or raises an exception if not found
    """
    val = getenv(var_name)
    if not val:
        raise Exception(f"can't find envvar {var_name}")
    return val


def main(message: func.ServiceBusMessage):

    thingspeak_keys = loads(getenv_or_exception("thingspeak_keys_dict"))
    thingspeak_api_endpoint = getenv_or_exception("thingspeak-api-endpoint")

    # Log the Service Bus Message as plaintext

    message_content_type = message.content_type
    message_body = loads(message.get_body().decode("utf-8"))
    send_message_to_thingspeak(message_body, thingspeak_keys, thingspeak_api_endpoint)
    

    logger.info("Python ServiceBus topic trigger processed message.")
    logger.info("Message Content Type: " + message_content_type)
    logger.info("Message Body: " + message_body)


def send_message_to_thingspeak(message: object, keys: dict, api_endpoint: str) -> None:

    headers = {"Content-Type": "application/json",
               "accept": "application/json`"}
    payload = create_payload_from_message(message, keys)

    response = requests.post(api_endpoint,
                             data=dumps(payload),
                             headers=headers)
    if not response.ok:
        raise Exception(
            f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")


def create_payload_from_message(message: object, keys: dict) -> object:
    api_key = keys[message["name"]]
    timestamp = message["datetime"]
    setpoint = message["heatSetpoint"]

    if (message["indoorTemperature"]) and (int(message["indoorTemperature"]) <= 60):
        temperature = message["indoorTemperature"]

    return {'api_key': api_key,
            "created_at": timestamp,
            'field1': temperature,
            "field2": setpoint}