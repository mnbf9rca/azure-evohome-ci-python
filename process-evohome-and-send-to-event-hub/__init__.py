import datetime
import logging
from os import getenv

import azure.functions as func
from azure.eventhub import EventData
from azure.eventhub.aio import EventHubProducerClient

#pylint: disable=relative-beyond-top-level
from ..evohome.EvohomeClient import EvohomeClient


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

    print(eh_usernamne)
