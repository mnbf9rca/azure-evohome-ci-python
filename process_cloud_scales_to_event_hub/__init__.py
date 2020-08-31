import logging
from json import dumps, loads

import azure.functions as func
from dateutil.parser import parse as dateutil_parse

logger = logging.getLogger(f"azure.func.{__name__}")

def main(event: func.EventHubEvent):
    logger.info(f'Processing message from cloud_scales event hub and pushing to event_hub')
    logger.debug('Python EventHub trigger processed an event: %s',
                 event.get_body().decode('utf-8'))
    message = loads(event.get_body().decode('utf-8'))
    logger.debug(f"received message: {message}")
    

    message['datetime'] = dateutil_parse(message['published_at']).timestamp()
    logger.debug(f'composed message {dumps(message)}')
    return dumps(message)
