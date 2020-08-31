import datetime
import logging
from json import dumps
from os import environ

import azure.functions as func

import typing

from .evohome import EvohomeClient

logger = logging.getLogger(f"azure.func.{__name__}")


# pylint: disable=unsubscriptable-object

def main(mytimer: func.TimerRequest) :
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logger.debug('The timer is past due!')

    logger.info('Python timer trigger function ran at %s', utc_timestamp)
    return process_evohome()


def process_evohome() -> typing.List[str]:

    # get config
    eh_usernamne = environ.get("evohome_username")
    eh_password = environ.get("evohome_password")
    eh_api_key = environ.get("evohome_api_key")

    # first, validate evohome connection
    ehc = EvohomeClient(username=eh_usernamne, password=eh_password, appid=eh_api_key)
    logger.debug(f"Successfully authenticated to evohome API as {eh_usernamne}")

    # get all locations
    all_locs = ehc.get_all_locations()
    logger.debug(f"found {len(all_locs)} locations")

    # now get all devices at all locations
    all_devices_all_locs = []
    for location in all_locs: 
        all_devices_all_locs = all_devices_all_locs + [{**{"type":"temperature"}, **data }for data in ehc.get_thermostat_temperatures(location["locationID"])]

    # create a list of strings to send as messages
    
    return [dumps(d) for d in all_devices_all_locs]


'''
def add_to_batch_and_send(device_list: dict) -> typing.List[str]:
    logger.info(f"processing batch for {len(device_list)} devices: {device_list}")
    for device in device_list:
        outputEventHubMessage.set(dumps(device).encode('utf-8'))
    logger.info("batch complete")
'''
