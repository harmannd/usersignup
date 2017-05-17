import os
import jinja2
import webapp2
import re

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return USER_RE.match(username)

PASSWORD_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return PASSWORD_RE.match(password)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **params):
        self.write(self.render_str(template, **params))

class MainPage(Handler):
    def get(self):
        self.render("signup.html")
    def post(self):
        self.redirect("/welcome")

class WelcomeHandler(Handler):
    def get(self):
        self.write("Welcome!")


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/welcome', WelcomeHandler)],
                                debug=True)