import logging
from datetime import datetime, timedelta
from json import dumps
from time import time
from typing import Tuple
import dateutil.parser

import requests

from helpers import urljoin


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
        logging.info("Initialising EvohomeClient")
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
        logging.info("requesting credentials")
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
            dict    of all locations following https://tccna.honeywell.com/WebApi/Help/Model/TrueHome.WebApi.Models.Responses.LocationResponse
        '''
        api_endpoint = 'api/locations'
        uri = urljoin(self._api_base, api_endpoint)
        headers = {"sessionId": self._session_token,
                   "accept": "application/json`"}
        query = {"userId": self._userID,
                 "allData": False}
        logging.info("requesting all locations")
        response = requests.get(url=uri,
                                headers=headers,
                                params=query)
        if not response.ok:
            raise Exception(
                f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
        return response.json()

    def get_one_location_data(self, locationId: int) -> dict:
        '''Fetches the device info for a given location.

        Accepts:
            locationId          identifier of the location
        Returns:
            LocationResponse    conforming to https://tccna.honeywell.com/WebApi/Help/Model/TrueHome.WebApi.Models.Responses.LocationResponse
        '''
        api_endpoint = 'api/locations'
        uri = urljoin(self._api_base, api_endpoint)
        headers = {"sessionId": self._session_token,
                   "accept": "application/json`"}
        query = {"locationId": locationId,
                 "allData": True}
        logging.info(f"requesting locations {locationId}")
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
            [{name, indoorTemperature, heatSetpoint}]
            datetime            posix timestamp of response
            deviceId            Identifier of the device.
            name    	        Device name.
            indoorTemperature  	Indoor temperature, if indoorTemperatureStatus='measured'.
            heatSetpoint      	Current heating setpoint.'''
        response_timestamp, this_location_data = self.get_one_location_data(locationId)
        temps = []
        for d in this_location_data["devices"]:
            this_temps = {'datetime': response_timestamp,
                          'deviceId': d["deviceID"],
                          'name': d["name"],
                          'heatSetpoint': d["thermostat"]["changeableValues"]["heatSetpoint"]["value"]}
            if d["thermostat"]["indoorTemperatureStatus"] == "Measured":
                this_temps.update({'indoorTemperature': d["thermostat"]["indoorTemperature"]})
            temps.append(this_temps)
        return temps
