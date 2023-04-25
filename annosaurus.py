import requests
import json
from typing import Dict


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

    def update_association(self,
                           uuid: str,
                           association: Dict,
                           client_secret: str = None,
                           jwt: str = None) -> Dict:

        jwt = self.authorize(client_secret, jwt)
        url = "{}/associations/{}".format(self.base_url, uuid)
        headers = self._auth_header(jwt)
        return requests.put(url, data=association, headers=headers).json()

    def delete_association(self,
                           uuid: str,
                           client_secret: str = None,
                           jwt: str = None) -> Dict:
        jwt = self.authorize(client_secret, jwt)
        url = "{}/associations/{}".format(self.base_url, uuid)
        headers = self._auth_header(jwt)
        requests.delete(url, headers=headers)
        print('Association deleted')

    def update_annotation(self,
                          observation_uuid: str,
                          updated_annotation: Dict,
                          client_secret: str = None,
                          jwt: str = None) -> str:
        possible_updates = ['identity-certainty', 'identity-reference', 'upon', 'comment', 'guide-photo']
        update_str = None
        jwt = self.authorize(client_secret, jwt)

        with requests.get(f'http://hurlstor.soest.hawaii.edu:8082/anno/v1/observations/{observation_uuid}') as r:
            if r.status_code != 200:
                return 'Unable to connect'
            old_annotation = r.json()
            # check for concept name change
            if updated_annotation['concept'] != old_annotation['concept']:
                url = "{}/annotations/{}".format(self.base_url, observation_uuid)
                update_str = 'Updated concept name\n'
                new_name = {
                    "concept": updated_annotation['concept']
                }
                headers = self._auth_header(jwt)
                requests.put(url, data=new_name, headers=headers)

            # get list of old association link_names that we can change
            old_link_names = []
            for old_association in old_annotation['associations']:
                if old_association['link_name'] in possible_updates:
                    old_link_names.append(old_association['link_name'])

            # get list of new link_names
            link_names_to_update = []
            for association in possible_updates:
                if updated_annotation[association] != '':
                    link_names_to_update.append(association)

            for link_name in link_names_to_update:
                if link_name in old_link_names:
                    # update the association
                    update_str += f'Updated association {link_name}\n'
                else:
                    # create new association
                    update_str += f'Added association {link_name}\n'

        return update_str if update_str else 'No changes made'
