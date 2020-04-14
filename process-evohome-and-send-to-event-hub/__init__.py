import datetime
import logging
from os import getenv

import azure.functions as func
from azure.eventhub import EventData, EventHubProducerClient, EventDataBatch


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
    eh_connection_string = getenv_or_exception("eventhub_cs_send")
    eh_name = getenv_or_exception("eventhub_name")
    eh_partition_evohome = getenv("eventhub_partition_evohome") # None is ok, no need for exception

    # first, validate evohome connection
    ehc = EvohomeClient(username=eh_usernamne, password=eh_password, appid=eh_api_key)
    logging.info(f"Successfully authenticated to evohome API as {eh_usernamne}")

    # now establish EventHubProducerClient
    client = EventHubProducerClient.from_connection_string(
        eh_connection_string,
        eventhub_name=eh_name)
    logging.info(f"Successfully create new EventHubProducerClient from eh_connection_string and eh_name: {client.get_eventhub_properties()}")


    # get all locations
    all_locs = ehc.get_all_locations()
    logging.info(f"found {len(all_locs)} locations")
    # now get all devices at all locations
    all_devices_all_locs = (ehc.get_thermostat_temperatures(location["locationID"]) for location in all_locs)

    # add to batches and send...
    for device_list in all_devices_all_locs: add_to_batch_and_send(device_list, client, eh_partition_evohome)

def add_to_batch_and_send(device_list: dict, client: EventHubProducerClient, partition_id: str) -> None:
    logging.info(f"processing batch for {len(device_list)} devices")
    event_data_batch = client.create_batch(partition_id=partition_id)
    for device in device_list:
        try:
            event_data_batch.add(EventData(device))
        except ValueError:
            # event_data_batch reached max size. Send and create new
            send_batch(client, event_data_batch)
            event_data_batch = client.create_batch(partition_id=partition_id)
            event_data_batch.add(EventData(device))
    # final batch
    send_batch(client, event_data_batch)
    logging.info("batch complete")

def send_batch(client: EventHubProducerClient, event_data_batch: EventDataBatch) -> None:
    logging.info(f"Sending batch of size {event_data_batch.size_in_bytes} - {event_data_batch._count} messages")
    with client:
        client.send_batch(event_data_batch)
    logging.info("batch sent")
