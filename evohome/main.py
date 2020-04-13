from dotenv import load_dotenv

from EvohomeClient import EvohomeClient
from helpers import getEnvVar

load_dotenv()
eh_username = getEnvVar("EH_USERNAME")
eh_password = getEnvVar("EH_PASSWORD")
eh_appid = getEnvVar("EH_APPID")

c = EvohomeClient(username=eh_username, password=eh_password, appid=eh_appid)
all_data = c.get_all_locations()
for location in all_data:
    this_location_data = c.get_thermostat_temperatures(location["locationID"])
    print(this_location_data)

