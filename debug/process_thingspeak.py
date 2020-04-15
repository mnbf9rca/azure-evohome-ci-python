from azure.servicebus import SubscriptionClient

from json import dumps, loads
from os import getenv
import logging
from dotenv import load_dotenv
import requests

from azure import functions as func
from azure.functions import ServiceBusMessage

from unittest import mock

logger = logging.getLogger()
logger.setLevel(logging.INFO)

load_dotenv()


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


sb_topic_name = getenv_or_exception("servicebus_evohome_topic")
conn_string = getenv_or_exception("func_thingspeak_servicebus_evohome_evohome-v2_conn_string")
sb_subscription = getenv_or_exception("func_thingspeak_servicebus_subscription")


sc = SubscriptionClient.from_connection_string(conn_string, sb_subscription)
logger.info("Created new SubscriptionClient")
r = sc.get_receiver(prefetch=2, mode="PREFETCH")
logger.info("Created receiver")
msg = r.fetch_next(timeout=5)
logger.info(f"received messages")
for m in msg:

    logger.info("processing message")
    this_message = {"body": m.body,
                    "content_type": m.properties.content_type,
                    "correlation_id": m.properties.correlation_id,
                    "delivery_count": m.message.delivery_no,
                    "expiration_time": m._expiry,
                    "label": None,
                    "message_id": m.properties.message_id,
                    "partition_key": m.partition_key,
                    "reply_to": m.properties.reply_to,
                    "reply_to_session_id": m.properties.reply_to_group_id,
                    "scheduled_enqueue_time": m.scheduled_enqueue_time,
                    "session_id": m.session_id,
                    "time_to_live": m.time_to_live,
                    "to": m.properties.to,
                    "user_properties": None}
    data = mock.Mock()
    data.type="string"
    data.value=str(m)
    x = func.servicebus.ServiceBusMessageInConverter.decode(data=data,
                                                            trigger_metadata=this_message)
    main(x)



