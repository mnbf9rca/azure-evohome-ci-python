import logging
from datetime import datetime, timedelta
from json import dumps
from time import time
from typing import Tuple

import requests

from helpers import urljoin


class EvohomeClient(object):
    '''Evohome v2 client'''

    def __init__(self, username: str, password: str, appid: str):
        '''Validate credentials, store token'''
        logging.info("Initialising EvohomeClient")
        self._api_base = 'https://tccna.honeywell.com/WebApi/'
        self._username = username
        self._password = password
        self._appid = appid
        self._userID, self._session_token = self._fetch_session_token()

    def _fetch_session_token(self) -> str:
        '''Fetches a session token from API\n
        Returns:\n
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
        return userID, sessionID

    def get_thermostat_data(self):
        '''Fetches thermostat data for all locations.'''
        api_endpoint = 'api/locations'
        uri = urljoin(self._api_base, api_endpoint)
        headers = {"sessionId": self._session_token,
                   "accept": "application/json`"}
        query = {"userId": self._userID,
                 "allData": True}
        logging.info("requesting all locations")
        response = requests.get(url=uri,
                                headers=headers,
                                params=query)
        if not response.ok:
            raise Exception(
                f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
        return response.json()
