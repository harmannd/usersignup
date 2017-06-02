import os
import jinja2
import webapp2
import re
import hmac

SECRET = 'imsosecret'

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    return "{}|{}".format(s, hash_str(s))

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")

def valid_username(username):
    return USER_RE.match(username)

def valid_password(password):
    return PASSWORD_RE.match(password)

def valid_email(email):
    if email == "":
        return True
    else:
        return EMAIL_RE.match(email)

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
        error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username = username,
                      email = email)

        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            error = True

        if not valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            error = True
        elif password != verify:
            params['error_verify_password'] = "Your passwords didn't match."
            error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            error = True

        if error:
            self.render('signup.html', **params)
        else:
            self.response.headers.add_header('Set-Cookie', 'user_id={}'.format(make_secure_val(username)))
            self.redirect('/welcome')


class WelcomeHandler(Handler):
    def get(self):
        username = self.request.cookies.get('user_id').split('|')[0]
        self.render('welcome.html', username = username)


app = webapp2.WSGIApplication([('/signup', MainPage),
                               ('/welcome', WelcomeHandler)],
                                debug=True)