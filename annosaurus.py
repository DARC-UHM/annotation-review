import requests
import json
from typing import Dict

from requests import Response


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
                           jwt: str = None) -> int:

        if 'link_name' not in association:
            raise ValueError(
                "association dict needs at least a 'link_name' key")
        jwt = self.authorize(client_secret, jwt)
        url = "{}/associations".format(self.base_url)
        association['observation_uuid'] = observation_uuid
        headers = self._auth_header(jwt)
        return requests.post(url, data=association, headers=headers).status_code

    def update_association(self,
                           uuid: str,
                           association: Dict,
                           client_secret: str = None,
                           jwt: str = None) -> int:

        jwt = self.authorize(client_secret, jwt)
        url = "{}/associations/{}".format(self.base_url, uuid)
        headers = self._auth_header(jwt)
        return requests.put(url, data=association, headers=headers).status_code

    def delete_association(self,
                           uuid: str,
                           client_secret: str = None,
                           jwt: str = None) -> int:
        jwt = self.authorize(client_secret, jwt)
        url = "{}/associations/{}".format(self.base_url, uuid)
        headers = self._auth_header(jwt)
        return requests.delete(url, headers=headers).status_code

    def update_annotation(self,
                          observation_uuid: str,
                          updated_annotation: Dict,
                          client_secret: str = None,
                          jwt: str = None) -> bool:
        possible_association_updates = ['identity-certainty', 'identity-reference', 'upon', 'comment', 'guide-photo']
        update_str = ''
        jwt = self.authorize(client_secret, jwt)
        success = True

        with requests.get(f'http://hurlstor.soest.hawaii.edu:8082/anno/v1/observations/{observation_uuid}') as r:
            if r.status_code != 200:
                return False
            old_annotation = r.json()

            # check for concept name change
            if updated_annotation['concept'] != old_annotation['concept']:
                url = "{}/annotations/{}".format(self.base_url, observation_uuid)
                update_str = 'Updated concept name\n'
                new_name = {
                    "concept": updated_annotation['concept']
                }
                headers = self._auth_header(jwt)
                if requests.put(url, data=new_name, headers=headers).status_code != 200:
                    success = False

            # get list of old association link_names that we can change
            old_link_names = []
            for old_association in old_annotation['associations']:
                if old_association['link_name'] in possible_association_updates:
                    old_link_names.append(old_association['link_name'])

            # get list of new link_names
            link_names_to_update = []
            for association in possible_association_updates:
                if updated_annotation[association] != '' or association in old_link_names:
                    link_names_to_update.append(association)

            for link_name in link_names_to_update:
                old_association = \
                    next((item for item in old_annotation['associations'] if item['link_name'] == link_name), None)
                if link_name in old_link_names:
                    if updated_annotation[link_name] == '':
                        # delete the association
                        if self.delete_association(uuid=old_association["uuid"], client_secret=client_secret) != 204:
                            success = False
                        update_str += f'Deleted association "{link_name}" UUID: {old_association["uuid"]}\n'
                    else:
                        # check if value actually changed
                        if link_name == 'upon' or link_name == 'guide-photo':
                            # 'upon' and 'guide-photo' use 'to_concept'
                            if old_association['to_concept'] != updated_annotation[link_name]:
                                # update the association
                                new_association = {'to_concept': updated_annotation[link_name]}
                                status = self.update_association(
                                    uuid=old_association['uuid'],
                                    association=new_association,
                                    client_secret=client_secret
                                )
                                if status != 200:
                                    success = False
                                update_str += f'Updated association "{link_name}" UUID: {old_association["uuid"]}\n'
                        else:
                            # others use 'link_value'
                            if old_association['link_value'] != updated_annotation[link_name]:
                                # update the association
                                new_association = {'link_value': updated_annotation[link_name]}
                                status = self.update_association(
                                    uuid=old_association['uuid'],
                                    association=new_association,
                                    client_secret=client_secret
                                )
                                if status != 200:
                                    success = False
                                update_str += f'Updated association "{link_name}" UUID: {old_association["uuid"]}\n'
                else:
                    # create new association
                    to_concept = \
                        updated_annotation[link_name] if link_name == 'upon' or link_name == 'guide-photo' else 'self'
                    link_value = \
                        'nil' if link_name == 'upon' or link_name == 'guide-photo' else updated_annotation[link_name]
                    new_association = {
                        'link_name': link_name,
                        'to_concept': to_concept,
                        'link_value': link_value
                    }
                    status = self.create_association(
                        observation_uuid=observation_uuid,
                        association=new_association,
                        client_secret=client_secret
                    )
                    if status != 200:
                        success = False
                    update_str += f'Added association "{link_name}"\n'

        print(update_str if update_str else 'No changes made')
        return success
