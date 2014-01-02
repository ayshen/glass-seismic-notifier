import util
import models


class DashboardHandler (util.TemplatingBaseHandler):
    """ Request handler for the location-of-interest manager.
    """

    @util.oauth_decorator.oauth_aware
    def get(self):
        if not util.oauth_decorator.has_credentials():
            self.redirect("/")

        # Try to get the current user's ID. This should work properly if the
        # user has authorized this application.
        try:
            user_id = models.User.info().get("id")
        except models.CredentialsException as e:
            self.redirect(e.authorization_url)

        # Get the locations in which the user is interested.
        locs = [{"key": loc.key.urlsafe(), "description": loc.description}
                for loc in models.LocationOfInterest.query_user(user_id)]

        # Render the dashboard.
        template_values = {"locations_of_interest": locs}
        self._render_template("dashboard.html", template_values)
