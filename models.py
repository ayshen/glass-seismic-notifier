import apiclient.discovery
import google.appengine.ext.db
import google.appengine.ext.ndb
import oauth2client.appengine

import util


class CredentialsException (Exception):
    """ Stub base class for exceptional conditions that may occur while trying
    to work with the user's profile information. """
    def __init__(self, authorization_url, ):
        self.authorization_url = authorization_url


class NotAuthorizedException (CredentialsException):
    """ Stub exception for trying to get the user information when the user
    has not authorized the application. """
    pass


class NoUserIdException (CredentialsException):
    """ Stub exception for having user info with no ID. """
    pass


class User (google.appengine.ext.ndb.Model):
    user_id = google.appengine.ext.ndb.StringProperty()

    @staticmethod
    def info():
        """ Get the current user's profile information. """

        # Fail if the user is not logged in.
        if not util.oauth_decorator.has_credentials():
            raise NotAuthorizedException(util.oauth_decorator.authorize_url())

        # Build the OAuth service to get the current user information.
        user_info_service = apiclient.discovery.build(
                serviceName="oauth2",
                version="v2",
                http=util.oauth_decorator.http())

        # Try to get the user's profile information from the Google OAuth
        # service.
        user_info = None
        try:
            user_info = user_info_service.userinfo().get().execute()
        except:
            raise CredentialsException(util.oauth_decorator.authorize_url())

        # Make sure the user information is actually useful (has an ID).
        if user_info and user_info.get("id"):
            return user_info
        else:
            raise NoUserIdException(util.oauth_decorator.authorize_url())


class LocationOfInterest (google.appengine.ext.ndb.Model):
    """ NDB model class for a location for which a user would like to receive
    notifications for earthquakes.

    In the interest of scalability, it might have been better to batch
    locations of interest by user ID, but I didn't want to figure it out.
    """

    # Schema.
    # * owner: the current user's ID.
    # * description: the human-readable description of location.
    # * location: the coordinates for which the current user would like to
    #   receive quake cards.
    owner = google.appengine.ext.ndb.StringProperty()
    description = google.appengine.ext.ndb.StringProperty()
    location = google.appengine.ext.ndb.GeoPtProperty()

    @classmethod
    def query_user(cls, user_id):
        """ Get locations of interest for a user based on the user's ID.

        cls: this class (util.LocationOfInterest).
        user_id (string): the current user's ID.
        """
        return cls.query(cls.owner == user_id)
