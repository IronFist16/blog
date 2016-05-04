import webapp2
import jinja2
from google.appengine.ext import db
import os

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
								autoescape=True)

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
	def render_main(self):
		entries = db.GqlQuery('SELECT * FROM BlogEntry ORDER BY timestamp DESC')
		#entries = BlogEntry.gql('ORDER BY timestamp DESC')
		self.render('Main.html', entries=entries)

	def get(self):
		self.render_main()

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



app = webapp2.WSGIApplication([
	('/', MainPage),
	('/newpost', NewPost),
	('/(\d+)', PostID)],
	debug=True)

