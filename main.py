import os
import webapp2
import json
from google.appengine.ext import ndb



## Datastore Models

class Player(ndb.Model):

    pid = ndb.StringProperty()
    name = ndb.StringProperty()
    a_url = ndb.IntegerProperty()
    tokens = ndb.IntegerProperty()
    cards_vis = ndb.JsonProperty(repeated=True)
    cards_inv = ndb.JsonProperty(repeated=True)


    def info_as_dict(self):

        return dict(
            ('name', self.name),
            ('id', self.pid),
            ('tokens', self.tokens),
            ('avatar_url', self.a_url),
            ('cards_visible', self.cards_vis),
            ('cards_not_visible', self.cards_inv))

    def gamestatus_as_dict(self):

        return dict(
            ('actions', self.actions()),
            ('your_cards_visible', self.cards_vis),
            ('common_cards_visible', ''),
            ('players', self.parent().get().players_as_dict())


class Game(ndb.Model):

    name = ndb.StringProperty()
    p_max = ndb.IntegerProperty()
    p_cur = ndb.IntegerProperty()
    state = ndb.IntegerProperty()


    def as_dict(self):

        return dict([
            ('name', self.name),
            ('id', self.key.id()),
            ('players_max', self.p_max),
            ('players_current', self.p_cur)])


    def players_as_dict(self):

        players = Player.query(ancestor=self.key).get()

        ret = list()
        for player in players:
            ret.append(player.info_as_dict())

        return ret



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
        new_game_in = json.loads(self.request.get('game'))

        # Make sure input is valid
        keys = ('id',
                'name',
                'players_max')
        if not all(key in new_game_in for key in keys):
            return

        new_game = Game(id=int(new_game_in['id']))
        new_game.populate(name = new_game_in['name'],
                          p_max = int(new_game_in['players_max']),
                          p_cur = 0,
                          state = 0)

        # Put it in the datastore
        new_game.put()


class GameIdPage(webapp2.RequestHandler):
    
    def get(self, gid):

        self.response.headers['Content/Type'] = 'text/html'
        self.response.out.write('{0}: i don\'t like it in here it\'s dark'.format(gid))


class PlayerConnectPage(webapp2.RequestHandler):

    def post(self, gid):
        
        sub_player = self.request.get('player')

        # Make sure input is valid
        keys = ('name',
                'id',
                'tokens',
                'avatar_url',
                'cards_visible',
                'cards_not_visible')
        if not all(key in sub_player for key in keys):
            return

        new_player = Person(id=int(sub_player['id']),
                            parent=ndb.Key('Game', gid))
        new_player.populate(name = sub_player['name'],
                            tokens = sub_player['tokens'],
                            a_url = sub_player['avatar_url'],
                            c_vis = sub_player['cards_visible'],
                            c_inv = sub_player['cards_not_visible'])
        new_player.put()


class StatusPage(webapp2.RequestHandler):
    
    def get(self, gid):

        pid = self.request.get('player_id')
        gkey = ndb.Key('Game', gid)
        player = Player.query(Player.pid == pid, ancestor=gkey).get()

        self.response.headers['Content/Type'] = 'application/json'
        self.response.out.write(json.dumps(player.gamestatus_as_dict()))



## Helper Functions



## Main Script

app = webapp2.WSGIApplication(
    [
        ('/games', GamePage),
        ('/games/([0-9]+)/', GameIdPage),
        ('/games/([0-9]+)/playerConnect', PlayerConnectPage)
        ('/games/([0-9]+)/status', StatusPage)
    ], debug=True)
