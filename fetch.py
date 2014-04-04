import base64
import datetime
import httplib2
import io
import json
import math
import random
import urllib2

import apiclient.discovery
import apiclient.http
import oauth2client.appengine
import webapp2

import util
import models


# URI for all earthquakes that occurred within the past hour.
QUAKE_DATA_URI = "http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

# Radius around a location of interest in which earthquakes are considered
# interesting.
RADIUS = 0.5 # geological degrees


def dist(a, b):
    return math.sqrt(math.pow(a[0] - b[0], 2) + math.pow(a[1] - b[1], 2))


def mapurl(quake):
    """ Make a URI for a static map of an earthquake location.
    The URI created by this function requests a static map from the Google
    Maps engine, centered around and with a marker at the epicenter of the
    given earthquake.
    """
    lon = float(quake[u"geometry"][u"coordinates"][0])
    lat = float(quake[u"geometry"][u"coordinates"][1])

    uri = "http://maps.googleapis.com/maps/api/staticmap"
    q = {
            "sensor": "false",
            "visual_refresh": "true",

            # Halve the image dimensions and ask for 2x scale because it's
            # easier to read on the tiny display.
            "size": "120x180",
            "scale": "2",

            # Zoom level might need to change if the user is interested in
            # places in the middle of the ocean, but it should be good
            # enough for most relatively developed areas.
            "zoom": "7",

            # Position is determined automatically by Google Maps.
            "markers": "size:mid%%7C%f,%f" % (lat, lon),
    }
    qs = "&".join(["%s=%s" % (k, q[k]) for k in q])

    return "%s?%s" % (uri, qs)

#("http://maps.googleapis.com/maps/api/staticmap?"
# "sensor=false&visual_refresh=true&size=120x180&scale=2&zoom=7&"
# "markers=size:mid%%7C%f,%f") % (lat, lon)


def make_bundle_cover(bundleId, cards):
    """ Make a static cover card for a list of earthquakes.
    TODO make this prettier. Right now just make a card declaring the
    number of earthquakes in this bundle.
    """
    return {
            "displayTime": datetime.datetime.utcnow().isoformat() + ".00+00:00",
            "html": "<article><section>%d earthquakes</section></article>" % len(cards),
            "menuItems": [{"action": "DELETE"}],
            "isBundleCover": True,
            "bundleId": bundleId,
    }


def make_card(quake, bundleId=None, ):
    """ Make a timeline card for an earthquake.

    quake (geojson): A GeoJSON fragment representing the earthquake.
    bundleId (str): The ID of the bundle into which this card will go.
    """
    # Get the important properties from the earthquake object.
    lon = float(quake[u"geometry"][u"coordinates"][0])
    lat = float(quake[u"geometry"][u"coordinates"][1])
    mag = float(quake[u"properties"][u"mag"])
    place = quake[u"properties"][u"place"]

    # Prepare the template for an earthquake notification card.
    template = util.get_template("quake.html")
    values = {"loc": place, "mag": mag}
    mapuri = mapurl(quake)

    # Compute the date and time of the earthquake.
    ms_since_epoch = quake[u"properties"][u"time"]
    sec_since_epoch = int(ms_since_epoch) / 1000
    quake_dt = datetime.datetime.utcfromtimestamp(sec_since_epoch)

    # Construct the object model for the card.
    # Notice that the map image needs to be attached to the card to work
    # properly.
    card = {
            "displayTime": quake_dt.isoformat() + ".00+00:00",
            "html": template.render(values),
            "attachments": [{
                    "contentType": "image/png",
                    "contentUrl": mapuri
            }],
            "menuItems": [{"action": "DELETE"}],
    }
    if bundleId is not None:
        card["bundleId"] = bundleId
        card["isBundleCover"] = False
    return card


def make_map(quake):
    """ Fetch a static map of an earthquake location. """
    try:
        return urllib2.urlopen(mapurl(quake)).read()
    except:
        return ""


class QuakeDataFetchHandler (webapp2.RequestHandler):
    def get(self):
        try:
            quake_data = json.loads(urllib2.urlopen(QUAKE_DATA_URI).read())
            self.process(quake_data)
        except urllib2.URLError:
            # Fail silently. This should be noisier, but most people won't care.
            pass

    def process(self, quake_data):
        """ Process a set of earthquakes.
        quake_data (geojson): The loaded earthquake GeoJSON.
        """
        last_updated = datetime.datetime.utcnow() - datetime.timedelta(0, 1800)

        # Find quakes that have occurred since the last time data was fetched.
        new_quakes = []
        for quake in quake_data[u"features"]:
            ms_since_epoch = quake[u"properties"][u"time"]
            sec_since_epoch = int(ms_since_epoch) / 1000
            quake_dt = datetime.datetime.utcfromtimestamp(sec_since_epoch)
            if quake_dt > last_updated:
                new_quakes.append(quake)
        self.send_notifications_for(new_quakes)

    def send_notifications_for(self, quakes):
        """ Create timeline entries for a set of earthquakes.

        quakes (list): A list of GeoJSON fragments representing individual
            earthquakes. These earthquakes may or may not be interesting to
            users.
        """
        for user in models.User.query():
            # Filter the new earthquakes to find the ones that are near places
            # that the user says are interesting.
            quakes_to_notify = []
            for quake in quakes:
                lon = float(quake[u"geometry"][u"coordinates"][0])
                lat = float(quake[u"geometry"][u"coordinates"][1])
                quakeloc = (lon, lat)
                for loi in models.LocationOfInterest.query(
                        models.LocationOfInterest.owner == user.user_id):
                    interestloc = (loi.location.lon, loi.location.lat)
                    if dist(quakeloc, interestloc) < RADIUS:
                        quakes_to_notify.append(quake)

            if len(quakes_to_notify) == 0:
                # The user isn't interested in any of the new earthquakes,
                continue

            # Create a (hopefully authorized) service connection to the
            # Mirror API, and insert cards for the earthquakes.
            credentials = oauth2client.appengine.StorageByKeyName(
                    oauth2client.appengine.CredentialsModel,
                    user.user_id,
                    "credentials").get()
            if credentials is None:
                continue
            authorized_http = credentials.authorize(httplib2.Http())
            mirror = apiclient.discovery.build(
                    serviceName="mirror", version="v1",
                    http=authorized_http)
            self.insert_quakes(mirror, quakes_to_notify)

    def insert_quakes(self, mirror, quakes):
        """ Insert cards for earthquakes into a timeline.

        mirror: A service connection to the Mirror API, authorized for a user.
        quakes (list): a list of GeoJSON representations of earthquakes.
        bundleId (str): the ID of the 
        """
        # Create a bundle ID. This has no effect if there's only one card,
        # but it will cause multiple notifications from the same fetch to
        # group together.
        bundleId = base64.b64encode(
                datetime.datetime.utcnow().isoformat() +
                chr(random.randint(0, 127)))

        # Make card object models and map image uploads for each earthquake.
        cards = []
        mediabodies = []
        for quake in quakes:
            cards.append(make_card(quake, bundleId))
            mediabodies.append(apiclient.http.MediaIoBaseUpload(
                    io.BytesIO(make_map(quake)),
                    mimetype="image/png",
                    resumable=True))

        # Batch-insert the earthquake cards into the timeline.
        timeline = mirror.timeline()
        for item in zip(cards, mediabodies):
            timeline.insert(body=item[0], media_body=item[1]).execute()

        # If there is more than one earthquake to send in this fetch, make a
        # cover card for the bundle that says how many earthquakes there are.
        if len(cards) > 1:
            timeline.insert(body=make_bundle_cover(bundleId, cards)).execute()

