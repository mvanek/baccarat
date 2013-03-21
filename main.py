import os
import webapp2
import jinja2
from google.appengine.ext import ndb



jinja_environment = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.dirname(__file__)))



## Datastore Models

class Player(ndb.Model):

    name = ndb.StringProperty()
    a_url = ndb.IntegerProperty()
    tokens = ndb.IntegerProperty()
    cards_vis = ndb.StringProperty(repeatable=True)
    cards_inv = ndb.StringProperty(repeatable=True)


    def as_dict(self):

        return dict(
            ('name', self.name),
            ('id', self.key()),
            ('tokens', self.tokens),
            ('avatar_url', self.a_url),
            ('cards_visible', self.cards_vis),
            ('cards_not_visible', self.cards_inv))


class Game(ndb.Model):

    name = ndb.StringProperty()
    p_max = ndb.IntegerProperty()
    p_cur = ndb.IntegerProperty()
    state = ndb.IntegerProperty()
    players = ndb.StructuredProperty(Player, repeated=True)


    def as_dict(self):

        return dict(
            ('name', self.name),
            ('id', self.key()),
            ('players_max', self.p_max),
            ('players_current', self.p_cur))



## Request Handlers

class GamePage(webapp2.RequestHandler):

    def get(self):

        # Get a list of all games
        games = Game.query()
        games_out = list()
        for game in games:
            games_out.append(game.as_dict())

        # Send the list to the user as JSON
        self.response.headers['Content/Type'] = 'application/json'
        self.response.out.write(json.dumps(games_out))


    def post(self):

        # Create a new game from the user's request
        new_game_in = json.loads(self.params('game'))
        new_game = Game(id = new_game_in['id'])
        new_game.populate(
            name = new_game_in['name'],
            p_max = new_game_in['players_max'],
            p_cur = 0,
            state = 0)

        # Put it in the datastore
        new_game.put()



## Helper Functions
