import logging
from json import dumps, loads

from requests import Response, post

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def send_message_to_thingspeak(message_body: dict, keys: dict, api_endpoint: str) -> None:
    logger.info(f"processing message: {message_body}")
    headers = {"Content-Type": "application/json",
               "accept": "application/json`"}
    
    payload = create_payload_from_message(message_body, keys)

    response = post(api_endpoint,
                    data=dumps(payload),
                    headers=headers)
    if not response.ok:
        raise Exception(
            f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")


def create_payload_from_message(message: dict, keys: dict) -> object:
    api_key = keys[message["name"]]
    timestamp = message["datetime"]
    setpoint = message["heatSetpoint"]

    if (message["indoorTemperature"]) and (int(message["indoorTemperature"]) <= 60):
        temperature = message["indoorTemperature"]

    return {'api_key': api_key,
            "created_at": timestamp,
            'field1': temperature,
            "field2": setpoint}
