""" Main application loader file.
"""

# Modify the search path for modules to include the libraries in lib/.
# Not really sure if everything in lib/ is necessary, but I don't want to poke
# around in there because everything works right now.
import sys
sys.path.insert(0, "lib")

# Import modules for working with Google services.
"""
* apiclient.discovey:       building service objects for working with the user's
                            profile info and Glass timeline.
* apiclient.http:           helper for attaching map images to quake cards.
* google.appengine.ext.ndb: data storage library for Google App Engine.
* jinja2:                   templating library used in conjunction with webapp2.
* oauth2client.appengine:   OAuth2 library for authorizing use of the user's
                            profile info and Glass timeline by this application.
* webapp2:                  request handlers for this application.
"""
import apiclient.discovery
import apiclient.http
import google.appengine.ext.ndb
import jinja2
import oauth2client.appengine
import webapp2

# Import the support classes and request handlers for each of the various parts
# of the application.
"""
* util:      Global objects and things upon which lots of other things depend.
* models:    Database model and user information helper.
* dashboard: Request handler for the location-of-interest management dashboard.
* loi:       Request handler for adding and deleting locations of interest.
* timeline:  Request handler for directly pushing (fake) quake cards.
"""
import util
import models
import dashboard
import loi
import timeline


class MainHandler (util.TemplatingBaseHandler):
    """ Request handler for the application root. Provides the splash/login
    page if the user has not authorized the application for the scopes listed
    in util.SCOPES. Redirects to /dashboard if authorized.
    """

    @util.oauth_decorator.oauth_aware
    def get(self):
        """ Handle a GET request for the application root.
        """
        if util.oauth_decorator.has_credentials():
            # User has authorized this application for the permissions listed in
            # util.SCOPES . Send them to the dashboard for managing locations.
            self.redirect("/dashboard")
        else:
            # Render the splash / login page.
            template_values = {"authorization_uri":
                    util.oauth_decorator.authorize_url()}
            self._render_template("index.html", template_values)


# All URI routing for the application.
ROUTES = [
    ("/", MainHandler),
    ("/dashboard", dashboard.DashboardHandler),
    ("/loi", loi.LocationOfInterestHandler),
    ("/timeline", timeline.TimelineHandler),
    (util.oauth_decorator.callback_path, util.oauth_decorator.callback_handler()),
]


# Define the application object, which App Engine will use to run
# the application.
app = webapp2.WSGIApplication(ROUTES, debug=True)

