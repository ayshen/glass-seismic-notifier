import json

import google.appengine.ext.ndb

import util
import models


class LocationOfInterestHandler (util.TemplatingBaseHandler):
    """ Request handler for managing a user's locations of interest.
    Provides actions for adding and deleting locations.
    """

    @util.oauth_decorator.oauth_aware
    def post(self):
        if not util.oauth_decorator.has_credentials():
            # Unauthorized to make API calls affecting the user.
            self.error(401)

        if self.request.get("action") == "put":
            # Try to get the coordinates.
            lng, lat = 0.0, 0.0
            try:
                lng = float(self.request.get("lng"))
                lat = float(self.request.get("lat"))
            except:
                self.error(400)
                return

            # Construct a new location of interest with the given parameters.
            loi = models.LocationOfInterest(
                    owner=models.User.info().get("id"),
                    description=self.request.get("loi"),
                    location=google.appengine.ext.ndb.GeoPt(lat, lng))

            # Add the location of interest.
            key = loi.put()
            self.redirect("/dashboard")

        elif self.request.get("action") == "delete":
            # Get the location's key and use it to delete the location.
            google.appengine.ext.ndb.Key(
                    urlsafe=self.request.get("key")).delete()
            self.redirect("/dashboard")

        else:
            # Strange action, not "put" or "delete". What could it be?
            # Doesn't matter, we won't be able to do what it says anyway.
            self.error(400)
