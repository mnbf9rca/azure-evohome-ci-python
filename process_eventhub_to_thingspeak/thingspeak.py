import logging
from json import dumps, loads

from requests import Response, post

logger = logging.getLogger()


def send_message_to_thingspeak(message_body: dict, keys: dict, api_endpoint: str) -> None:
    '''processes a single message by parsing the data elements and submitting to thingspeak via API

        Accepts:
            message_body    the message body from the event hub
            keys            dict of name:api_key values for each thingspeak channel
            api_endpoint    thingspeak API URL

        Returns:
            None. Raises an exception if thingspeak API does not return an "ok" response.
    '''
    logger.info(f"processing message: {message_body}")
    headers = {"Content-Type": "application/json",
               "accept": "application/json`"}

    payload = create_payload_from_message(message_body, keys)

    response = post(api_endpoint,
                    data=dumps(payload),
                    headers=headers)
    if not response.ok:
        raise Exception(
            f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")


def create_payload_from_message(message: dict, keys: dict) -> dict:
    '''creates a data submission payload for a single message to submit to thingspeak

        Accepts:
            message     the message with data to submit
            keys        dict of name:api_key values for each thingspeak channel

        Returns:
            dict {api_key, created_at, field1 ... fieldn}:
            api_key     relevant thingspeak channel API key
            created_at  timestamp from the message
            fieldn      relevant data fields mapped according to message type
        '''
    api_key = keys[message["name"]]
    timestamp = message["datetime"]

    data_fields = get_fields(message)
    logger.info(f"data_fields: {dumps(data_fields)}")
    metadata_fields = {'api_key': api_key,
                       "created_at": timestamp}

    return {**metadata_fields, **data_fields}


def get_fields(message: dict) -> dict:
    '''Returns the data fields for thingspeak based on the message type
        accepts:
            message:    message
        returns:
            dict of field:value pairs'''
    if message["type"] == "temperature":
        ''' Temperature data from evohome
            field1: temperature
            field2: setpoint
            '''
        if (message["indoorTemperature"]) and (int(message["indoorTemperature"]) <= 60):
            temperature = message["indoorTemperature"]

        return {'field1': temperature,
                'field2': message["heatSetpoint"]}

    elif message["type"] == "energy":
        ''' gas/electricity consumption from hildebrand
            field1: gas_consumption
            field2: gas_cost
            field3: electricity_consumption
            field4: electricity_cost
            '''
        return {'field1': message['gas_consumption'],
                "field2": message['gas_cost'],
                "field3": message['electricity_consumption'],
                "field4": message['electricity_cost']}

    elif message["type"] == "cloud_scales":
        ''' weight measurements from scales 
            field1: average/value
            field2: average/units
            field3: temperature'''
        result = {}
        if message['event'] == "average/value":
            result['field1'] = message['data']
        elif message['event'] ==  "average/units":
            result['field2'] = message['data']

        else:
            raise ValueError(f"Unable to understand event type: '{message['event']}'")
        if "temperature" in message:
            result['field3'] = message['temperature']         

        return result   
    else:
        # dont know this message type
        raise ValueError(f"Message type not known: {message['type']}")
