import cgi
import webapp2
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import users
from google.appengine.ext import ndb

import MySQLdb
import os
import jinja2

import urllib

from datetime import date, datetime

"""Defined here are the ProtoRPC messages needed to define Schemas for methods
as well as those methods defined in an API.
"""
import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote


# Configure the Jinja2 environment.
JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  autoescape=True,
  extensions=['jinja2.ext.autoescape'])


DEFAULT_GUESTBOOK_NAME = 'default_guestbook'


# We set a parent key on the 'Greetings' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Guestbook', guestbook_name)


class SkillsInterests(ndb.Model):
    """Models people's interests/skills, and date."""
    user_id = ndb.IntegerProperty()
    skill_interest = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

  # @classmethod
  # def query_skillsinterests(cls, ancestor_key):
  #  return cls.query(ancestor=ancestor_key).order(-cls.date)


# for EndPoints APIs
package = 'Hello'

class Greeting(messages.Message):
    """Greeting that stores a message."""
    message = messages.StringField(1)

class GreetingCollection(messages.Message):
    """Collection of Greetings."""
    items = messages.MessageField(Greeting, 1, repeated=True)

STORED_GREETINGS = GreetingCollection(items=[
    Greeting(message='hello world!'),
    Greeting(message='goodbye world!'),
])


# Define your production Cloud SQL instance information.
_INSTANCE_NAME = 'road-719:hostappDB'

class MainPage(webapp2.RequestHandler):
    def get(self):
        # Display existing guestbook entries and a form to add new entries.
        if (os.getenv('SERVER_SOFTWARE') and
            os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')):
            db = MySQLdb.connect(unix_socket='/cloudsql/' + _INSTANCE_NAME, db='hostappDB', user='root')
        else:
            db = MySQLdb.connect(host='127.0.0.1', port=3306, db='hostappDB', user='root')
            # Alternately, connect to a Google Cloud SQL instance using:
            # db = MySQLdb.connect(host='ip-address-of-google-cloud-sql-instance', db='hostappDB', port=3306, user='root')

        cursor = db.cursor()
        cursor.execute('SELECT first_name, last_name, user_id, email, City, LinkedIn, start_date FROM userinfo')

        # Create a list of guestbook entries to render with the HTML.
        guestlist = [];
        for row in cursor.fetchall():
          qry = SkillsInterests.query(SkillsInterests.user_id == row[2])
          skillsintersts = '' 
          for new_entry in qry:
               skillsintersts += new_entry.skill_interest+', '
               # self.response.out.write('<blockquote>%s, %d, %d </blockquote>' %
               #               (cgi.escape(skillsintersts), new_entry.user_id, row[2] ))
               # self.response.out.write('---- this is a test ----')

          guestlist.append(dict([('firstname',cgi.escape(row[0])),
                                 ('lastname',cgi.escape(row[1])),
                                 ('ID',row[2]),
                                 ('startdate', (row[6])),
                                 ('email',(row[3])),
                                 ('city',(row[4])),
				 ('LinkedIn',(row[5])),
				 ('SkillsInterests', (skillsintersts)) 
                                 ]))

        variables = {'guestlist': guestlist}
        template = JINJA_ENVIRONMENT.get_template('main.html')
        self.response.write(template.render(variables))
        db.close()

class Guestbook(webapp2.RequestHandler):
    def post(self):
        # Handle the post to create a new guestbook entry.
        fname = self.request.get('fname')
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        email = self.request.get('email')
        street = self.request.get('street')
        city = self.request.get('city')
        state = self.request.get('state')
        country = self.request.get('country')
        linkedin = self.request.get('linkedin')
        content = self.request.get('content')

        if (os.getenv('SERVER_SOFTWARE') and
            os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')):
            db = MySQLdb.connect(unix_socket='/cloudsql/' + _INSTANCE_NAME, db='hostappDB', user='root')
        else:
            db = MySQLdb.connect(host='127.0.0.1', db='hostappDB', port=3306, user='root')
            # Alternately, connect to a Google Cloud SQL instance using:
            # db = MySQLdb.connect(host='ip-address-of-google-cloud-sql-instance', port=3306, user='root')

        cursor = db.cursor()
        # Note that the only format string supported is %s
        today = datetime.now().date()
	cursor.execute('INSERT INTO userinfo (first_name, last_name, email, street, city, state, country, linkedin, start_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', (first_name, last_name, email, street, city, state, country, linkedin, today))
        newID = cursor.lastrowid
	db.commit()
        db.close()

	new_skillsinterests = SkillsInterests()
        new_skillsinterests.user_id = newID
        new_skillsinterests.skill_interest = 'programming %d' % newID
        new_skillsinterests.put()
 
        self.redirect("/")

application = webapp2.WSGIApplication([('/', MainPage),
                               ('/sign', Guestbook)],
                              debug=True)

def main():
    application = webapp2.WSGIApplication([('/', MainPage),
                                           ('/sign', Guestbook)],
                                          debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()




