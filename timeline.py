# Import global modules.
"""
* datetime: Date and time utilities. Used to fake a time for the fake quake
            cards, but will also be useful for handling actual quake data.
* io:       BytesIO, for packaging map images for attachment to the
            Mirror API request.
* urllib2:  fetching map images from the Google Static Maps API.
"""
import datetime
import io
import urllib2

# Import modules for working with Google APIs.
"""
* apiclient.discovery: building the Mirror service object.
* apiclient.http:      packaging attachments for API requests.
"""
import apiclient.discovery
import apiclient.http

# Import the template support function, authorization decorator, and base
# request handler.
import util


def quakemap(lng, lat):
    """ Generate a URI for requesting a map of the epicenter of a quake
    from the Google Static Maps API.

    lng (float): longitude of the epicenter.
    lat (float): latitude of the epicenter.
    """
    return ("http://maps.googleapis.com/maps/api/staticmap?"
            "sensor=false&visual_refresh=true&size=120x180&scale=2&zoom=7&"
            "markers=size:mid%%7C%f,%f") % (lat, lng)


class TimelineHandler (util.TemplatingBaseHandler):
    """ Request handler for directly pushing (fake) quake cards to the user's
    Glass timeline.
    """

    @util.oauth_decorator.oauth_aware
    def get(self):
        """ Render the form for constructing a fake quake card. """
        if not util.oauth_decorator.has_credentials():
            self.redirect("/")
        self._render_template("timeline.html", {})

    @util.oauth_decorator.oauth_aware
    def post(self):
        """ Publish a fake quake card. """
        if not util.oauth_decorator.has_credentials():
            self.error(403)

        # Request a service object for the Mirror API.
        mirror = apiclient.discovery.build(
                serviceName="mirror",
                version="v1",
                http=util.oauth_decorator.http())

        # Generate the API request body.
        card = self.quake_card()
        mapimg = self.map_image()

        # Create a helper for attaching the map image to the API request.
        media_body = apiclient.http.MediaIoBaseUpload(io.BytesIO(mapimg),
                mimetype="image/png", resumable=True)

        # Publish the quake card to the user's Glass timeline.
        timeline_transaction = mirror.timeline()
        timeline_transaction.insert(body=card, media_body=media_body).execute()

    def map_image(self):
        """ Fetch a map of the epicenter of the requested quake. """
        try:
            return urllib2.urlopen(quakemap(*self.coords())).read()
        except:
            return ""

    def coords(self):
        """ Get the coordinates of the epicenter of the requested quake. """
        try:
            return ( float(self.request.get("lng")),
                    float(self.request.get("lat")) )
        except:
            return (0.0, 0.0)

    def quake_card(self):
        """ Generate an API request for publishing a quake card. """
        template = util.get_template("quake.html")

        # Figure out what to substitute in the template for quake cards.
        values = {"loc": self.request.get("loc"), "mag": 0.0}
        try:
            values["mag"] = float(self.request.get("mag"))
        except:
            pass

        # Create the API request body.
        mapurl = quakemap(*self.coords())
        return {
                "displayTime": datetime.datetime.utcnow().isoformat() + "Z",
                "html": template.render(values),
                "attachments": [{"contentType": "image/png", "contentUrl": mapurl}],
                "menuItems": [{"action": "DELETE"}],
        }
