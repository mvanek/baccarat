import logging
import random
import os
import webapp2
import json
from google.appengine.ext import ndb

## Data Models
from card import Card
from deck import Deck
from player import Player
from game import Game


## Request Handlers

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

    def post(self, gid):
        
        sub_player = json.loads(self.request.get('player'))

        # Make sure input is valid
        keys = ('name',
                'id',
                'tokens',
                'avatar_url')
        if not all(key in sub_player for key in keys):
            self.response.headers['Content/Type'] = 'text/plain'
            self.response.out.write('error')
            return

        # Store the new player in the datastore
        this_game = Game.get_by_id(gid)
        if not this_game:
            self.response.headers['Content/Type'] = 'text/plain'
            self.response.out.write('error')
            return
        this_game.p_cur += 1

        gkey = this_game.key

        new_player = Player(id=sub_player['id'], parent=gkey)
        new_player.populate(name = sub_player['name'],
                            tokens = int(sub_player['tokens']),
                            a_url = sub_player['avatar_url'],
                            cards_vis = sub_player['cards_visible'],
                            cards_inv = sub_player['cards_not_visible'],
                            sync = 4)

        new_player.put()
        this_game.put()

        # Send response
        self.response.headers['Content/Type'] = 'text/plain'
        self.response.out.write('ok')



class StatusPage(webapp2.RequestHandler):
    
    def get(self, gid):

        Game.get_by_id(gid).selfupdate()

        pid = self.request.get('player_id')
        if not pid: 
            return

        player = ndb.Key('Game', gid,
                         'Player', pid).get()

        self.response.headers['Content/Type'] = 'application/json'

        if player:
            self.response.out.write(json.dumps(player.gamestatus_as_dict()))



class ActionPage(webapp2.RequestHandler):

    def post(self, gid):

        pid = self.request.get('player_id')
        act = self.request.get('action')
        val = self.request.get('value')

        if pid:
            player = ndb.Key('Game', gid, 'Player', pid).get()

        if player:
            player.do_action(act, val)



class TablePage(webapp2.RequestHandler):

    def get(self, gid):

        self.response.headers['Content/Type'] = 'text/html'
        self.response.out.write('this is a beautiful mahogany table.')



## Main Script

app = webapp2.WSGIApplication([
    ('/games', GamePage),
    ('/games/([0-9]+)/', GameIdPage),
    ('/games/([0-9]+)/playerConnect', PlayerConnectPage),
    ('/games/([0-9]+)/visible_table', TablePage),
    ('/games/([0-9]+)/action', ActionPage),
    ('/games/([0-9]+)/status', StatusPage)], debug=True)
