import webapp2
import jinja2
from google.appengine.ext import db
import os
import hashlib
import hmac
import string
import random

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
								autoescape=True)
SECRET = 'imsosecret'

def make_salt():
	return ''.join([random.choice(string.letters) for i in range(5)])

def make_pw_hash(name, pw, salt=None):
	if not h:
		salt = make_salt()
	hsh = hashlib.sha256(name+pw+salt).hexdigest()
	return '{}|{}'.format(hsh,salt)

def valid_pw(name, pw, h):
	salt = h.split('|')[1]
	return h == make_pw_hash(name, pw, salt)

def hash_str(s):
	#return hashlib.md5(s).hexdigest()
	return hashlib.md5(s).hexdigest()

def make_secure_val(s):
	h = hash_str(s)
	return '{}|{}'.format(s, h)

def check_secure_val(h):
	s, hsh = h.split('|')
	if make_secure_val(s) == h:
		return s
	else:
		return None

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **param):
		t = jinja_env.get_template(template)
		return t.render(**param)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

class BlogEntry(db.Model):
	author = db.StringProperty()
	subject = db.StringProperty(required=True)
	content = db.TextProperty(required=True)
	timestamp = db.DateTimeProperty(auto_now_add=True)
	link = db.StringProperty()


class MainPage(Handler):
	def render_main(self, visits):
		entries = db.GqlQuery('SELECT * FROM BlogEntry ORDER BY timestamp DESC')
		#entries = BlogEntry.gql('ORDER BY timestamp DESC')
		self.render('Main.html', entries=entries, visits=visits)

	def get(self):
		visits_cookie_str = self.request.cookies.get('visits')
		visits = 0
		if visits_cookie_str:
			cookie_val = check_secure_val(visits_cookie_str)
			if cookie_val:
				visits = int(cookie_val) 
		
		visits += 1
		new_cookie_val = make_secure_val(str(visits))
		self.response.headers.add_header('Set-Cookie', 'visits=%s' % 
								new_cookie_val)

		self.render_main(visits)


class NewPost(Handler):
	def render_entry(self, subject='', author='ANONYMOUS', content='', error=''):
		self.render('newpost.html', subject=subject, author=author, content=content, error=error)

	def get(self):
		self.render_entry()

	def post(self):
		author = self.request.get('author')
		subject = self.request.get('subject')
		content = self.request.get('content')
		if subject and content:
			entry = BlogEntry(author=author, subject=subject, content=content)
			entry.put()
			entry_id = entry.key().id()
			self.redirect('/'+str(entry_id))
		else:
			error_msg = "Both Subject and Content are required !"
			self.render_entry(subject, author, content, error=error_msg)



class PostID(Handler):
	def render_post(self, subject='', author='ANONYMOUS', content=''):
		self.render('post.html', subject=subject, author=author, content=content)
	
	def get(self, id):
		entry = BlogEntry.get_by_id(long(id))
		self.render_post(subject=entry.subject,
						author=entry.author,
						content=entry.content)

class Registration(Handler):
	def render_register(self, username='', password='', verify='', email=''):
		self.render('registration.html', username=username, password=password,
					verify=verify, email=email)

	def get(self):
		self.render_register()



app = webapp2.WSGIApplication([
	('/', MainPage),
	('/newpost', NewPost),
	('/(\d+)', PostID),
	('/registration', Registration)],
	debug=True)

