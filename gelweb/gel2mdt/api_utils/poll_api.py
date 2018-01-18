import os
import getpass
import requests
import json

import labkey as lk


class PollAPI(object):
    """
    Representation of an instance when an API has been polled. Contains info
    about the reponse including repsonse code, the json that has been returned,
    the API that has been polled.
    """
    def __init__(self, api, endpoint):
        self.api = api
        self.endpoint = endpoint

        self.server_list = {
            "cip_api": (
                "https://cipapi.genomicsengland.nhs.uk/api/2/{endpoint}",
                True),
            "panelapp": (
                "https://panelapp.genomicsengland.co.uk/WebServices/{endpoint}",
                False),
            "ensembl": (
                "http://rest.ensembl.org/{endpoint}",
                False),
            "mutalyzer": (
                "https://mutalyzer.nl/json/{endpoint}",
                False)}

        self.server = self.server_list[api][0]
        self.url = self.server.format(endpoint=self.endpoint)
        self.headers = None  # headers will be set if required, denoted in server_list tuple

        self.token_url = None  # only need this if auth headers required
        self.response = self.get_json_response(url=self.url, headers=self.server_list[api][1])
        self.response_status = None

    def get_json_response(self, url, headers):
        """
        Creates a session which polls the instance's API a maximum of 20 times
        for a json response, retrying if the poll fails.
        """

        while True:
            # set up request session to retry failed connections
            MAX_RETRIES = 20
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES)
            session.mount("https://", adapter)

            if (headers) and (self.headers is None):
                # get auth headers if we need them and they're not yet set
                self.get_auth_headers()
                continue
            elif (headers) and (self.headers is not None):
                # auth headers required; have been set
                response = session.get(
                    url=url,
                    headers=self.headers)
            elif headers is None:
                # no headers required
                response = session.get(
                    url=url)

            self.response_status = response.status_code
            return response.json()

    def get_credentials(self):
        """
        Asks user for username and password and sets these as environment variables to be accessed later.
        """
        os.environ["cip_api_username"] = input("Enter username: ")
        os.environ["cip_api_password"] = getpass.getpass("Enter password: ")

    def get_auth_headers(self):
        """
        Creates a token then uses this to get authentication headers for CIP-API"
        """
        token_endpoint_list = {
            "cip_api": "get-token/"}
        token_endpoint = token_endpoint_list[self.api]

        self.token_url = self.server.format(endpoint=token_endpoint)
        print(self.token_url)
        self.get_credentials()
        token_response = requests.post(
            url=self.token_url,
            json=dict(
                username=os.environ["cip_api_username"],
                password=os.environ["cip_api_password"]
            ),
        )

        token_json = token_response.json()

        print(token_json)
        self.headers = {
            "Accept": "application/json",
            "Authorization": "JWT {token}".format(
                token=token_json.get("token"))}