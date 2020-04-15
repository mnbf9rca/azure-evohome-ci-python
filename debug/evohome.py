
import logging
from json import dumps
from os import getenv

from azure.servicebus import Message, TopicClient
from dotenv import load_dotenv
from EvohomeClient import EvohomeClient

logger = logging.getLogger("azure.eventhub")
logger.addFilter(logging.Filter(__name__))
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


def process_evohome() -> None:

    # get config
    eh_usernamne = getenv_or_exception("evohome_username")
    eh_password = getenv_or_exception("evohome_password")
    eh_api_key = getenv_or_exception("evohome_api_key")
    servicebus_evohome_conn_string = getenv_or_exception(
        "func_send_servicebus_evohome_evohome-v2_conn_string")
    sb_topic_name = getenv_or_exception("servicebus_evohome_topic")

    # create a topic client to send items to the servicebus topic
    topic_client = TopicClient.from_connection_string(servicebus_evohome_conn_string, sb_topic_name)
    logger.info(f"Successfully created TopicClient for {topic_client.address }")

    # first, validate evohome connection
    ehc = EvohomeClient(username=eh_usernamne, password=eh_password, appid=eh_api_key)
    logger.info(f"Successfully authenticated to evohome API as {eh_usernamne}")

    # get all locations
    all_locs = ehc.get_all_locations()
    logger.info(f"found {len(all_locs)} locations")
    # now get all devices at all locations
    all_devices_all_locs = (ehc.get_thermostat_temperatures(
        location["locationID"]) for location in all_locs)

    # add to batches and send...
    for device_list in all_devices_all_locs:
        add_to_batch_and_send(device_list, topic_client)


def add_to_batch_and_send(device_list: dict, client: TopicClient) -> None:
    logger.info(f"processing batch for {len(device_list)} devices")
    messages = [Message(dumps(device).encode('utf-8')) for device in device_list]
    logger.info(f"{len(messages)} messages queued")
    client.send(messages=messages)
    logger.info("batch complete")


process_evohome()
