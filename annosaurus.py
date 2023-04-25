import requests
import json
from typing import Dict, List
from datetime import datetime


class AuthenticationError(Exception):
    """
    Exception raised for errors during authentication.
    """

    def __init__(self, message):
        """
        :param str message:  explanation of the error
        """
        self.message = message


class JWTAuthentication(object):

    def __init__(self, base_url: str):
        if base_url.endswith("/"):
            base_url = base_url[0:-1]
        self.base_url = base_url

    def authorize(self, client_secret: str, jwt: str) -> str:
        """Fetch a JWT authentication token if needed """
        if jwt:
            pass
        elif client_secret:
            jwt = self.authenticate(client_secret)
        else:
            raise AuthenticationError("No jwt or client_secret were provided")

        if not jwt:
            raise AuthenticationError(
                "Failed to authenticate with your client_secret")
        return jwt

    def authenticate(self, client_secret: str) -> str:
        """Call the authentication endpoint to retrieve a JWT token as a string"""
        url = "{}/auth".format(self.base_url)
        headers = {"Authorization": "APIKEY {}".format(client_secret)}

        r = requests.post(url, headers=headers)
        try:
            auth_response = r.json()
            return auth_response["access_token"]
        except json.decoder.JSONDecodeError:
            print("-- BAD Authentication: {} returned: \n{}".format(url, r.text))
            return ''

    def _auth_header(self, jwt: str) -> Dict:
        """Format """
        return {"Authorization": "Bearer " + jwt}


class Annosaurus(JWTAuthentication):
    """
    Encapsulate REST calls to the annotation service
    """

    def __init__(self, base_url: str):
        JWTAuthentication.__init__(self, base_url)

    def create_annotation(self,
                          video_reference_uuid: str,
                          concept: str,
                          observer: str,
                          elapsed_time_millis: int = None,
                          recorded_timestamp: datetime = None,
                          timecode: str = None,
                          client_secret: str = None,
                          jwt: str = None) -> Dict:

        jwt = self.authorize(client_secret, jwt)
        headers = self._auth_header(jwt)
        data = {"video_reference_uuid": video_reference_uuid,
                "concept": concept,
                "observer": observer}
        if elapsed_time_millis:
            data['elapsed_time_millis'] = elapsed_time_millis
        elif recorded_timestamp:
            data['recorded_timestamp'] = "{}".format(
                recorded_timestamp.isoformat())
        elif timecode:
            data['timecode'] = timecode

        url = "{}/annotations".format(self.base_url)
        r = requests.post(url, data=data, headers=headers)
        print(r)
        print(r.text)
        print(data)
        return r.json()

        # return requests.post(url, data=data, headers=headers).json()

    def create_association(self,
                           observation_uuid: str,
                           association: Dict,
                           client_secret: str = None,
                           jwt: str = None) -> Dict:

        if 'link_name' not in association:
            raise ValueError(
                "association dict needs at least a 'link_name' key")

        jwt = self.authorize(client_secret, jwt)
        url = "{}/associations".format(self.base_url)
        association['observation_uuid'] = observation_uuid
        headers = self._auth_header(jwt)
        return requests.post(url, data=association, headers=headers).json()

    def update_annotation(self,
                          annotation: Dict,
                          client_secret: str = None,
                          jwt: str = None) -> Dict:
        jwt = self.authorize(client_secret, jwt)
        url = "{}/annotations/{}".format(self.base_url, annotation['observation_uuid'])
        updated_annotation = {
            "concept": annotation['concept']
        }
        headers = self._auth_header(jwt)
        r = requests.put(url, data=updated_annotation, headers=headers)
        print(r)
        print(r.text)
        return r.json()

    def delete_annotation(self,
                          observation_uuid: str,
                          client_secret: str = None,
                          jwt: str = None):
        jwt = self.authorize(client_secret, jwt)
        headers = self._auth_header(jwt)
        url = "{}/observations/{}".format(self.base_url, observation_uuid)
        return requests.delete(url, headers=headers)
