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
        if base_url.endswith('/'):
            base_url = base_url[0:-1]
        self.base_url = base_url

    def authorize(self, client_secret: str = None, jwt: str = None) -> str:
        """
        Fetch a JWT authentication token if needed
        """
        if jwt:
            pass
        elif client_secret:
            jwt = self.authenticate(client_secret)
        else:
            raise AuthenticationError('No jwt or client_secret were provided')

        if not jwt:
            raise AuthenticationError('Failed to authenticate with your client_secret')
        return jwt

    def authenticate(self, client_secret: str) -> str:
        """
        Call the authentication endpoint to retrieve a JWT token as a string
        """

        url = f'{self.base_url}/auth'
        res = requests.post(
            url=url,
            headers={'Authorization': f'APIKEY {client_secret}'},
        )
        try:
            auth_response = res.json()
            return auth_response['access_token']
        except json.decoder.JSONDecodeError:
            print(f'-- BAD Authentication: {url} returned: \n{res.text}')
            return ''

    def _auth_header(self, jwt: str) -> Dict:
        """
        Format
        """
        return {'Authorization': f'Bearer {jwt}'}


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
                           jwt: str = None) -> dict:

        if 'link_name' not in association:
            raise ValueError('association dict missing key "link_name"')
        jwt = self.authorize(client_secret, jwt)
        association['observation_uuid'] = observation_uuid
        if "link_value" not in association or association["link_value"] is None:
            association["link_value"] = "nil"
        res = requests.post(
            url=f'{self.base_url}/associations',
            data=association,
            headers=self._auth_header(jwt),
        )
        # print(association)
        # print(res.text)
        return {'status': res.status_code, 'json': res.json()}

    def update_association(self,
                           association_uuid: str,
                           association: Dict,
                           client_secret: str = None,
                           jwt: str = None) -> dict:

        jwt = self.authorize(client_secret, jwt)
        res = requests.put(
            url=f'{self.base_url}/associations/{association_uuid}',
            data=association,
            headers=self._auth_header(jwt),
        )
        return {'status': res.status_code, 'json': res.json()}

    def delete_association(self,
                           association_uuid: str,
                           client_secret: str = None,
                           jwt: str = None) -> dict:

        jwt = self.authorize(client_secret, jwt)
        res = requests.delete(
            url=f'{self.base_url}/associations/{association_uuid}',
            headers=self._auth_header(jwt),
        )
        return {'status': res.status_code, 'json': {}}

    def update_concept_name(self,
                            observation_uuid: str,
                            concept: str,
                            client_secret: str = None,
                            jwt: str = None) -> dict:

        jwt = self.authorize(client_secret, jwt)
        res = requests.put(
            url=f'{self.base_url}/annotations/{observation_uuid}',
            data={'concept': concept},
            headers=self._auth_header(jwt),
        )
        return {'status': res.status_code, 'json': res.json()}

    def update_annotation_comment(self,
                                  observation_uuid: str,
                                  reviewers: list,
                                  client_secret: str = None,
                                  jwt: str = None) -> dict:
        jwt = self.authorize(client_secret, jwt)
        res = requests.get(url=f'{self.base_url}/observations/{observation_uuid}')
        if res.status_code != 200:
            print(f'Unable to find annotation with observation uuid of {observation_uuid}')
            return {'status': res.status_code, 'json': res.json()}

        comment_association = next((item for item in res.json()['associations'] if item['link_name'] == 'comment'), None)
        if comment_association:
            # there's already a comment
            old_comment = comment_association['link_value'].split('; ')
            old_comment = [cmt for cmt in old_comment if 'send to' not in cmt.lower()]  # get rid of 'send to expert' notes
            old_comment = [cmt for cmt in old_comment if 'added for review' not in cmt.lower()]  # get rid of old 'added for review' notes
            old_comment = '; '.join(old_comment)
            if old_comment:
                if reviewers:  # add reviewers to the current comment
                    new_comment = f'{old_comment}; Added for review: {", ".join(reviewers)}'
                else:  # remove reviewers from the comment
                    new_comment = old_comment
            elif reviewers:  # create a new comment with reviewers
                new_comment = f'Added for review: {", ".join(reviewers)}'
            else:  # remove the comment
                new_comment = ''

            new_association = {'link_value': new_comment}
            if new_comment == '':
                # delete the comment
                deleted = self.delete_association(
                    association_uuid=comment_association['uuid'],
                    jwt=jwt,
                )
                if deleted['status'] != 204:
                    print('Error deleting comment')
                else:
                    print('Deleted comment')
                return deleted
            else:
                updated = self.update_association(
                    association_uuid=comment_association['uuid'],
                    association=new_association,
                    jwt=jwt,
                )
                if updated['status'] != 200:
                    print('Error updating comment')
                else:
                    print('Updated comment')
                return updated
        else:
            # make a new comment
            new_comment = f'Added for review: {", ".join(reviewers)}'
            comment_association = {
                'link_name': 'comment',
                'link_value': new_comment
            }
            created = self.create_association(
                observation_uuid=observation_uuid,
                association=comment_association,
                jwt=jwt
            )
            if created['status'] != 200:
                print('Error creating comment')
            else:
                print('Created comment')
            return created
