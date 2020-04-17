from requests import post, Response
from json import dumps


def send_message_to_thingspeak(message: dict, keys: dict, api_endpoint: str) -> None:

    headers = {"Content-Type": "application/json",
               "accept": "application/json`"}
    payload = create_payload_from_message(message, keys)

    response = post(api_endpoint,
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