import logging
from json import dumps

import dateutil.parser
import requests

logger = logging.getLogger()


def urljoin(*args):
    """
    Joins given arguments into an url. Trailing but not leading slashes are
    stripped for each argument.
    """

    return "/".join(map(lambda x: str(x).rstrip('/'), args))


class EvohomeClient(object):
    '''Evohome client conforming to https://tccna.honeywell.com/WebApi/Help with session IDs (not OAuth)

    Accepts:
        username        User's username - email.
        password        User's password
        ApplicationId   Application Id of clients application.

    Returns:
        Instantiated object
    '''

    def __init__(self, username: str, password: str, appid: str):
        '''Validate credentials, store token'''
        logger.debug("Initialising EvohomeClient")
        self._api_base = 'https://tccna.honeywell.com/WebApi/'
        self._username = username
        self._password = password
        self._appid = appid
        self._userID, self._session_token = self._fetch_session_token()

    def _fetch_session_token(self) -> (int, str):
        '''Fetches a session token from API

        Returns:
            (userID, SessionId)
            userID      User's unique identifier
            SessionId   Session id is used for each request after successfull authentication'''
        api_endpoint = 'api/session'
        uri = urljoin(self._api_base, api_endpoint)
        SessionRequest = {"Username": self._username,
                          "Password": self._password,
                          "ApplicationId": self._appid}
        headers = {"Content-Type": "application/json",
                   "accept": "application/json`"}
        logger.debug("requesting credentials")
        response = requests.post(uri,
                                 data=dumps(SessionRequest),
                                 headers=headers)
        if not response.ok:
            raise Exception(
                f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
        userID = response.json()["userInfo"]["userID"]
        sessionID = response.json()["sessionId"]
        return (userID, sessionID)

    def get_all_locations(self) -> dict:
        '''Fetches all locations

        Accepts:
            None
        Returns:
            dict of {name: str, locationID: int}    of all locations
        '''
        api_endpoint = 'api/locations'
        uri = urljoin(self._api_base, api_endpoint)
        headers = {"sessionId": self._session_token,
                   "accept": "application/json`"}
        query = {"userId": self._userID,
                 "allData": False}
        logger.debug("requesting all locations")
        response = requests.get(url=uri,
                                headers=headers,
                                params=query)
        if not response.ok:
            raise Exception(
                f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
        return [{"name": x["name"], "locationID": x["locationID"]} for x in response.json()]

    def get_one_location_data(self, locationId: int) -> dict:
        '''Fetches the device info for a given location.

        Accepts:
            locationId          identifier of the location
        Returns:
            response_timestamp  posix timestamp of response
            LocationResponse    conforming to https://tccna.honeywell.com/WebApi/Help/Model/TrueHome.WebApi.Models.Responses.LocationResponse
        '''
        api_endpoint = 'api/locations'
        uri = urljoin(self._api_base, api_endpoint)
        headers = {"sessionId": self._session_token,
                   "accept": "application/json`"}
        query = {"locationId": locationId,
                 "allData": True}
        logger.debug(f"requesting locations {locationId}")
        response = requests.get(url=uri,
                                headers=headers,
                                params=query)
        if not response.ok:
            raise Exception(
                f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
        response_timestamp = int(dateutil.parser.parse(response.headers["Date"]).timestamp())
        return response_timestamp, response.json()

    def get_thermostat_temperatures(self, locationId: int) -> dict:
        '''Fetches the current name, indoorTemperature and heatSetpoint for each device at a location

        Accepts:
            locationId  identifier of the location

        Returns
            locationId
            list of {datetime, deviceId, name, heatSetpoint[, indoorTemperature]]}
            datetime            posix timestamp of response
            deviceId            Identifier of the device.
            name    	        Device name.
            heatSetpoint      	Current heating setpoint.
            indoorTemperature  	Indoor temperature, only if indoorTemperatureStatus='measured'.'''
        response_timestamp, this_location_data = self.get_one_location_data(locationId)
        temps = []
        for d in this_location_data["devices"]:
            this_temps = {'locationId': locationId,
                          'datetime': response_timestamp,
                          'deviceId': d["deviceID"],
                          'name': d["name"],
                          'heatSetpoint': d["thermostat"]["changeableValues"]["heatSetpoint"]["value"]}
            if d["thermostat"]["indoorTemperatureStatus"] == "Measured":
                this_temps.update({'indoorTemperature': d["thermostat"]["indoorTemperature"]})
            temps.append(this_temps)
        return temps