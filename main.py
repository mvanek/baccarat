import jinja2
import os
import random
import webapp2
import json
from google.appengine.ext import ndb
from google.appengine.api import channel

## Data Models
from player import Player
from game import Game
from deck import Deck
from card import Card



jinja_environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))



## Request Handlers

class ResetPage(webapp2.RequestHandler):

    def get(self):

        players = Player.query()
        games = Game.query()
        cards = Card.query()
        decks = Deck.query()

        ndb.delete_multi([p for p in players.iter(keys_only=True)])
        ndb.delete_multi([g for g in games.iter(keys_only=True)])
        ndb.delete_multi([c for c in cards.iter(keys_only=True)])
        ndb.delete_multi([d for d in decks.iter(keys_only=True)])

        self.response.headers['Content/Type'] = 'text/html'
        self.response.out.write('Deleted everything. Smooth move.')


class ChannelPage(webapp2.RequestHandler):

    def get(self, gid):

        pid = self.request.get('player_id')

        if pid:
            self.response.headers['Content/Type'] = 'application/json'
            self.response.out.write(channel.create_channel(pid))


class GamePage(webapp2.RequestHandler):

    def get(self):

        # Get a list of all games
        games = Game.query()
        games_out = [game.as_dict() for game in games]

        # Send the list to the user as JSON
        self.response.headers['Content/Type'] = 'application/json'
        self.response.out.write(json.dumps(games_out))


    def post(self):

        new_game_in = json.loads(self.request.get('game'))

        # Make sure input is valid
        keys = ('id',
                'name',
                'players_max')
        if not all(key in new_game_in for key in keys):
            return

        # Create a new game and put it into the datastore
        Game.new(new_game_in['id'],
                 new_game_in['name'],
                 int(new_game_in['players_max']))



class GameIdPage(webapp2.RequestHandler):

    def get(self, gid):

        self.response.headers['Content/Type'] = 'text/html'
        self.response.out.write('{0}: i don\'t like it in here it\'s dark'.format(gid))



class PlayerConnectPage(webapp2.RequestHandler):

    def senderror(self):

        self.response.headers['Content/Type'] = 'text/plain'
        self.response.out.write('error')


    def post(self, gid):

        sub_player = json.loads(self.request.get('player'))

        # Make sure input is valid
        keys = ('name',
                'id',
                'tokens')

        if not all(key in sub_player for key in keys):
            self.senderror()
            return

        # Check if the game exists
        this_game = Game.get_by_id(gid)
        if not this_game:
            self.senderror()
            return

        # Check if player ID is taken
        player = Player.get_by_id(sub_player['id'])
        if player:
            self.senderror()
            return

        # Store the new player in the datastore
        new_player = Player(id=sub_player['id'],
                            name = sub_player['name'],
                            tokens = int(sub_player['tokens']),
                            a_url = sub_player['avatar_url'],
                            cards_vis = sub_player['cards_visible'],
                            cards_inv = sub_player['cards_not_visible'],
                            sync = 4)
        pkey = new_player.put()

        if not pkey:
            self.senderror()
            return

        this_game.p_cur += 1
        this_game.players.append(pkey)
        this_game.put()

        # Send response
        self.response.headers['Content/Type'] = 'text/plain'
        self.response.out.write('ok')



class StatusPage(webapp2.RequestHandler):

    def get(self, gid):

        game = Game.get_by_id(gid)

        pid = self.request.get('player_id')
        if not pid:
            return

        player = Player.get_by_id(pid)
        if not player:
            return

        self.response.headers['Content/Type'] = 'application/json'

        if player:
            self.response.out.write(json.dumps(game.gamestatus_as_dict(player)))



class ActionPage(webapp2.RequestHandler):

    def post(self, gid):

        game = Game.get_by_id(gid)
        if not game:
            return

        pid = self.request.get('player_id')
        act = self.request.get('action')
        val = self.request.get('value')


        if pid:
            player = Player.get_by_id(pid)

        if player:
            player.do_action(game, act, val)



class TablePage(webapp2.RequestHandler):

    def get(self, gid):

        players = Game.get_by_id(gid).players_as_dict()

        tvars = {'players': players}
        template = jinja_environment.get_template('/templates/table.html')

        self.response.headers['Content/Type'] = 'text/html'
        self.response.out.write(template.render(tvars))



## Main Script

app = webapp2.WSGIApplication([
    ('/reset', ResetPage),
    ('/games', GamePage),
    ('/games/([0-9]+)/', GameIdPage),
    ('/games/([0-9]+)/status_channel_open', ChannelPage),
    ('/games/([0-9]+)/playerConnect', PlayerConnectPage),
    ('/games/([0-9]+)/visible_table', TablePage),
    ('/games/([0-9]+)/action', ActionPage),
    ('/games/([0-9]+)/status', StatusPage)], debug=True)
