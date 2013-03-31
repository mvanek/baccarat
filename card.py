from google.appengine.ext import ndb

class Card(ndb.Model):

    draws = ndb.IntegerProperty(default=0)


    def deck(self):

        return self.key.parent().get()

