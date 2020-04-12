from dotenv import load_dotenv

from EvohomeClient import EvohomeClient
from helpers import getEnvVar

load_dotenv()
eh_username = getEnvVar("EH_USERNAME")
eh_password = getEnvVar("EH_PASSWORD")
eh_appid = getEnvVar("EH_APPID")

c = EvohomeClient(username=eh_username, password=eh_password, appid=eh_appid)
print(c.get_thermostat_data())