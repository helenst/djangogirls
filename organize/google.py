import logging
import os.path
from httplib2 import Http

from django.conf import settings
from django.utils.crypto import get_random_string

from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


logger = logging.getLogger(__name__)


DIRECTORY_SCOPE = 'https://www.googleapis.com/auth/admin.directory.user'

"""
Several things were needed to get this working:
1. Create an app in Developer Console
2. Create a service account to enable 2 legged oauth (https://developers.google.com/identity/protocols/OAuth2ServiceAccount)
3. Enable delegation of domain-wide authority for the service account.
4. Enable Admin SDK for the domain.
5. Give the service account permission to access admin.directory.users service (https://admin.google.com/AdminHome?chromeless=1#OGX:ManageOauthClients).
"""


def generate_password(length=12):
    return get_random_string(length=length)


def make_email(slug):
    """Get the email address for the given slug"""
    return '%s@djangogirls.org' % slug


class GoogleUsersAPI:
    def __init__(self):
        self._service = None
        self.authenticate()

    def authenticate(self):
        filename = settings.GOOGLE_API_CREDENTIALS_FILE
        if filename and os.path.isfile(filename):
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                settings.GOOGLE_API_CREDENTIALS_FILE,
                scopes=DIRECTORY_SCOPE,
            )

            credentials = credentials.create_delegated(settings.GOOGLE_API_DELEGATED_EMAIL)
            http_auth = credentials.authorize(Http())

            self._service = build('admin', 'directory_v1', http=http_auth)
        else:
            logger.warn('Google credentials file %s does not exist', filename)

    @property
    def is_ok(self):
        return self._service is not None

    def create_account(self, slug, city_name, password):
        """
        Create a new account

        e.g. create_account('testcity', 'Test City')

        Raises HttpError 409 if city already exists.
        """
        email = make_email(slug)

        response = self._service.users().insert(body={
            "primaryEmail": email,
            "name": {
                "fullName": "Django Girls %s" % city_name,
                "givenName": "Django Girls",
                "familyName": city_name,
            },
            "password": password,
        }).execute()

        logger.info('Account %s created with password %s', email, password)

        return response

    def rename_account(self, old_slug, new_slug):
        """
        Rename an account

        e.g. rename_account('testcity', 'testcity1')
        """
        old_email = make_email(old_slug)
        new_email = make_email(new_slug)

        response = self._service.users().patch(
            userKey=old_email,
            body={
                "primaryEmail": new_email,
            },
        ).execute()

        # The old email address is kept as an alias to the new one, but we don't want this.
        self._service.users().aliases().delete(userKey=new_email, alias=old_email).execute()

        logger.info('Account %s renamed to %s', old_email, new_email)

        return response
