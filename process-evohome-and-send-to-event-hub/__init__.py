import datetime
import logging
from os import getenv

import azure.functions as func
from azure.servicebus import ServiceBusClient, Message as SBC_message, TopicClient
from azure.servicebus.control_client import ServiceBusService, Message as SBS_Message
from json import dumps


#pylint: disable=relative-beyond-top-level
from ..EvoHome.EvohomeClient import EvohomeClient

logger = logging.getLogger("azure.eventhub")


def getenv_or_exception(var_name: str) -> str:
    """
    fetches an environment variable or raises an exception if not found
    """
    val = getenv(var_name)
    if not val:
        raise Exception(f"can't find envvar {var_name}")
    return val


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

    # get config
    eh_usernamne = getenv_or_exception("evohome_username")
    eh_password = getenv_or_exception("evohome_password")
    eh_api_key = getenv_or_exception("evohome_api_key")
    servicebus_namespace = getenv_or_exception("servicebus_namespace")
    servicebus_shared_access_key_name = getenv_or_exception("servicebus_shared_access_key_name")
    servicebus_shared_access_key_value = getenv_or_exception("servicebus_shared_access_key_value")
    sb_topic_name = getenv_or_exception("servicebus_topic_name")

    # first, validate evohome connection
    ehc = EvohomeClient(username=eh_usernamne, password=eh_password, appid=eh_api_key)
    logging.info(f"Successfully authenticated to evohome API as {eh_usernamne}")

    # now establish client
    servicebus_client = ServiceBusClient(service_namespace=servicebus_namespace,
                               shared_access_key_name=servicebus_shared_access_key_name,
                               shared_access_key_value=servicebus_shared_access_key_value)
    
    logging.info(
        f"Successfully create new ServiceBusClient with shared_access_key {servicebus_shared_access_key_name} to {servicebus_client.service_namespace}")
    topic_client = servicebus_client.get_topic(sb_topic_name)
    logging.info(f"Successfully created TopicClient for {topic_client.address }")

    # get all locations
    all_locs = ehc.get_all_locations()
    logging.info(f"found {len(all_locs)} locations")
    # now get all devices at all locations
    all_devices_all_locs = (ehc.get_thermostat_temperatures(
        location["locationID"]) for location in all_locs)

    # add to batches and send...
    for device_list in all_devices_all_locs:
        add_to_batch_and_send(device_list, topic_client)


def add_to_batch_and_send(device_list: dict, client: TopicClient) -> None:
    logging.info(f"processing batch for {len(device_list)} devices")
    
    messages = [SBC_message(dumps(device).encode('utf-8')) for device in device_list]
    client.send(messages=messages)
    logging.info("batch complete")
