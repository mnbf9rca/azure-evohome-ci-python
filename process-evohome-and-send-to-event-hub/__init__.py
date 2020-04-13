import datetime
import logging

import azure.functions as func
from azure.eventhub import EventData
from azure.eventhub.aio import EventHubProducerClient

from evohome.EvohomeClient import EvohomeClient
from evohome.helpers import getEnvVar

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
    eh_usernamne = getEnvVar("evohome_username")

    print(eh_usernamne)
    
    

