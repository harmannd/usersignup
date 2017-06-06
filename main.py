import os
import jinja2
import webapp2
import re
import hmac
import hashlib
import random

from string import letters
from google.appengine.ext import db

SECRET = 'imsosecret'
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

def valid_username(username):
    return USER_RE.match(username)

def valid_password(password):
    return PASSWORD_RE.match(password)

def valid_email(email):
    if email == "":
        return True
    else:
        return EMAIL_RE.match(email)





def make_secure_val(val):
    return "{}|{}".format(val, hmac.new(SECRET, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val




def make_salt():
    return ''.join(random.choice(letters) for x in xrange(5))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    hexhash = hashlib.sha256(name + pw + salt).hexdigest()
    return '{},{}'.format(hexhash, salt)

def valid_pw(name, password, hexhash_salt):
    salt = hexhash_salt.split(',')[1]
    return hexhash_salt == make_pw_hash(name, password, salt)





class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

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
            pw_hash = make_pw_hash(username, password)
            u = User(name = username, pw_hash = pw_hash, email = email)
            u.put()

            self.response.headers.add_header('Set-Cookie', 'user_id={}; Path=/'.format(make_secure_val(str(u.key().id()))))
            self.redirect('/welcome')

class WelcomeHandler(Handler):
    def get(self):
        user_id = self.request.cookies.get('user_id').split('|')[0]
        if user_id:
            username = User.get_by_id(int(user_id)).name
            self.render('welcome.html', username = username)
        else:
            self.redirect('/signup')

class LoginHandler(Handler):
    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        users = db.GqlQuery("SELECT * FROM User "
                           "WHERE name = :1", username).fetch(limit = None)

        if username and password and len(users) > 0:
            for user in users:
                if valid_pw(username, password, user.pw_hash):
                    self.response.headers.add_header('Set-Cookie', 'user_id={}; Path=/'.format(make_secure_val(str(user.key().id()))))
                    self.redirect('/welcome')
        else:
            self.render('login.html', invalid = "Invalid login")

class LogoutHandler(Handler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        self.redirect('/signup')


app = webapp2.WSGIApplication([('/signup', MainPage),
                               ('/welcome', WelcomeHandler),
                               ('/login', LoginHandler),
                               ('/logout', LogoutHandler)],
                                debug=True)