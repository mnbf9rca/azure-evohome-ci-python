import datetime
import logging
from json import dumps
from os import getenv

import azure.functions as func

from .evohome import EvohomeClient

logger = logging.getLogger("azure.func")


def getenv_or_exception(var_name: str) -> str:
    """
    fetches an environment variable or raises an exception if not found
    """
    val = getenv(var_name)
    if not val:
        raise Exception(f"can't find envvar {var_name}")
    return val

# pylint: disable=unsubscriptable-object


def main(mytimer: func.TimerRequest, outputEventHubMessage: func.Out[str]) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logger.info('The timer is past due!')

    logger.info('Python timer trigger function ran at %s', utc_timestamp)
    process_evohome(outputEventHubMessage)


def process_evohome(outputEventHubMessage: func.Out[str]) -> None:

    # get config
    eh_usernamne = getenv_or_exception("evohome_username")
    eh_password = getenv_or_exception("evohome_password")
    eh_api_key = getenv_or_exception("evohome_api_key")

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
        add_to_batch_and_send(device_list,outputEventHubMessage)


def add_to_batch_and_send(device_list: dict, outputEventHubMessage: func.Out[str]) -> None:
    logger.info(f"processing batch for {len(device_list)} devices")
    for device in device_list:
        outputEventHubMessage.set(dumps(device).encode('utf-8'))
    logger.info("batch complete")
