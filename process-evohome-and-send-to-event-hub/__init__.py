import datetime
import logging
from os import getenv

import azure.functions as func
from azure.eventhub import EventData, EventHubProducerClient


#pylint: disable=relative-beyond-top-level
from ..EvoHome.EvohomeClient import EvohomeClient


def getEnvVar(var_name):
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
    eh_usernamne = getEnvVar("evohome_username")
    eh_password = getEnvVar("evohome_password")
    eh_api_key = getEnvVar("evohome_api_key")
    eh_connection_string = getEnvVar("eventhub_cs_send")
    eh_name = getEnvVar("eventhub_name")

    # first, validate evohome connection
    ehc = EvohomeClient(username=eh_usernamne, password=eh_password, appid=eh_api_key)
    logging.info(f"Successfully authenticated to evohome API as {eh_usernamne}")

    # now establish EventHubProducerClient
    client = EventHubProducerClient.from_connection_string(
        eh_connection_string,
        eventhub_name=eh_name)
    logging.info("Successfully create new EventHubProducerClient from eh_connection_string and with eh_name")

    all_locs = ehc.get_all_locations()
    event_data_batch = client.create_batch()

    for location in all_locs:
        this_location_data = ehc.get_thermostat_temperatures(location["locationID"])
        for device in this_location_data:
            try:
                event_data_batch.add(EventData(device))
            except ValueError:
                # event_data_batch reached max size. Send and create new
                
                
                logging.info(f"Sending batch of size {event_data_batch.size_in_bytes} - {event_data_batch._count} messages")
                client.send_batch(event_data_batch)
                logging.info("batch sent")
                event_data_batch = client.create_batch()
                event_data_batch.add(EventData(device))
    
    # final batch
    logging.info(f"Sending batch of size {event_data_batch.size_in_bytes} - {event_data_batch._count} messages")
    client.send_batch(event_data_batch)
    logging.info("batch sent")
