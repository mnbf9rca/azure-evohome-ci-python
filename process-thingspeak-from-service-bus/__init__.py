import logging

import azure.functions as func
import azure.functions.blob as b


def main(message: func.ServiceBusMessage):
    # Log the Service Bus Message as plaintext

    message_content_type = message.content_type
    message_body = message.get_body().decode("utf-8")

    logging.info("Python ServiceBus topic trigger processed message.")
    logging.info("Message Content Type: " + message_content_type)
    logging.info("Message Body: " + message_body)




def getEnvVar(var_name):
    """
    fetches an environment variable or raises an exception if not found
    """
    val = getenv(var_name)
    if not val:
        raise Exception(f"can't find envvar {var_name}")
    return val