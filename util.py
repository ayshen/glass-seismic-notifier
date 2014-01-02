import os

import jinja2
import oauth2client.appengine
import webapp2


# OAuth2 permission scopes and request handler decorator.
# Rather magical.
SCOPES = [
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/glass.timeline",
]
oauth_decorator = oauth2client.appengine.OAuth2DecoratorFromClientSecrets(
        "client_secrets.json", SCOPES)


# jinja2 environment for loading and rendering templates for the
#application pages and timeline cards.
jinja_environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


def get_template(filename):
    return jinja_environment.get_template(
            os.path.join("templates", filename))


class TemplatingBaseHandler (webapp2.RequestHandler):
    """ Base class for some request handlers for this application.
    Defines a template rendering function.
    """

    def _render_template(self, filename, template_values, ):
        """ Simple helper to render a template.

        filename (str): name of the template, inside /templates/.
        template_values (dict): values to render in the template.
        """
        template = get_template(filename)
        self.response.out.write(template.render(template_values))
