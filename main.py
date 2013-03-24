import random
import os
import webapp2
import json
from google.appengine.ext import ndb



## Datastore Models

class Card(ndb.Model):

    draws = ndb.IntegerProperty(default=0)


    def deck(self):

        return self.key.parent().get()


    def map_value(self):

        myid = (self.key.id() - self.deck().start_card) % 13

        if myid is 0:
            return {1, 11}
        if myid < 10:
            return {myid - 1}
        else:
            return {10}


    def as_cardstr(self):
        
        myid = self.key.id() - self.deck().start_card
        
        # First get suit
        if myid < 13:
            suit = 'h'
            myid = 13 - myid
        elif myid < 26:
            suit = 'd'
            myid = 26 - myid
        elif myid < 39:
            suit = 's'
            myid = 39 - myid
        else:
            suit = 'c'
            myid = 52 - myid

        # Then get number
        if myid is 0:
            val = 'A'
        elif myid < 10:
            val = str(val-1)
        elif myid is 10:
            val = 'J'
        elif myid is 11:
            val = 'Q'
        elif myid is 12:
            val = 'K'

        return val + suit



class Deck(ndb.Model):

    num_decks = ndb.IntegerProperty()
    start_card = ndb.IntegerProperty()

    @classmethod
    def new(self, num_decks, parent_key):

        new_deck = Deck(num_decks=num_decks, parent=parent_key)

        first, last = Card.allocate_ids(52)
        new_deck.start_card = first

        new_deck.put()
        ndb.put_multi([Card(parent=new_deck.key, id=ind) \
            for ind in range(first, last+1)])
            
        return new_deck.key


    @ndb.transactional
    def draw(self):
        cards = Card.query(Card.draws < self.num_decks,
                           ancestor=self.key).fetch(52)
        ret = random.choice(cards)
        ret.draws += 1
        ret.put()
        return ret



class Player(ndb.Model):

    name = ndb.StringProperty()
    a_url = ndb.StringProperty()
    tokens = ndb.IntegerProperty()
    bet = ndb.IntegerProperty()
    cards_vis = ndb.KeyProperty(repeated=True)
    cards_inv = ndb.KeyProperty(repeated=True)
    cards_spl = ndb.KeyProperty(repeated=True)

    # Sync values:
    #   0 => Player has not yet taken any action
    #   1 => Player has acted, but is not standing
    #   2 => Player is standing
    #   3 => Player has surrendered
    #   4 => Player has joined game but is not playing
    sync = ndb.IntegerProperty()


    def game(self):
        
        return self.key.parent().get()


    def gamestatus_as_dict(self):

        cvis = [card.get().as_cardstring() for card in self.cards_vis]
        cinv = [card.get().as_cardstring() for card in self.cards_inv]

        return {'actions': self.actions(),
                'your_cards_visible': cvis,
                'common_cards_visible': [],
                'players': self.game().players_as_dict()}


    def info_as_dict(self):

        cvis = [card.get().as_cardstring() for card in self.cards_vis]
        cinv = [card.get().as_cardstring() for card in self.cards_inv]

        return {'name': self.name,
                'id': self.key.id(),
                'tokens': self.tokens,
                'avatar_url': self.a_url,
                'cards_visible': cvis,
                'cards_not_visible': cinv}


    def hand_values(self):

        values = set()

        for card in self.cards_vis:
            values = {a+b for a in card.map_value() for b in values}

        return values


    def actions(self):

        if self.sync < 2 and self.game().playing:
            ret = ['hit',
                   'stand',
                   'doubledown']

            if self.sync is 0:
                ret.append('surrender')

                if cards_vis[0] is cards_vis[1]:
                    ret.append('split')

            return ret

        elif self.sync is 4:
            return ['join']
        else:
            return []


    def do_action(self, act, val):

        if act not in self.actions():
            return

        dispatch = self.getattr('__{}'.format(act))
        dispatch()
        if self.sync is 0:
            self.sync = 1
        self.put()

        self.game().selfupdate()


    def __hit(self, val):
        gkey = self.key.parent()
        deck = Deck.query(parent=gkey).get()
        card = deck.draw()

        # Add card to hand
        self.cards_vis.append(card.key)


    def __stand(self, val):
        self.sync = 2


    def __doubledown(self, val):

        # Double your wager
        self.wager += wager

        # Take a single card
        self.__hit(val)

        # And stand
        self.__stand(val)


    def __split(self, val):

        # Set up the two different decks
        self.cards_spl.append(self.cards_vis.pop())


    def __surrender(self, val):

        # Mark self as surrendered
        self.sync = 3


    def __join(self, val):

        # Set proper sync value
        self.sync = 0

        # Submit bet
        self.bet = val
        self.tokens -= val

        # Get two cards
        self.__hit(val)
        self.__hit(val)



class Game(ndb.Model):

    name = ndb.StringProperty()
    p_max = ndb.IntegerProperty()
    p_cur = ndb.IntegerProperty()
    playing = ndb.BooleanProperty()


    @classmethod
    def new(self, gid, name, p_max):
        oldgame = Game.get_by_id(gid)
        if oldgame:
            return oldgame.key

        new_game = Game(id=gid,
                        name = name,
                        p_max = p_max,
                        p_cur = 0)
        new_game.put()

        Deck.new(1, new_game.key)

        return new_game.key


    def as_dict(self):

        return {'name': self.name,
                'id': self.key.id(),
                'players_max': self.p_max,
                'players_current': self.p_cur}


    def players_as_dict(self):

        def callback(self, player): return player.info_as_dict()

        return Player.query(ancestor=self.key).map(
            lambda player: player.info_as_dict())


    def selfupdate(self):

        # Check if the round is done
        players = Player.query(Player.sync > 1, ancestor=self.key)
        if players.count(self.p_cur) is self.p_cur:
            self.finish_round()

        # Send notification messages to connected clients
        self.notify_players()


    def start_round(self):

        self.playing = True
        self.put()

        self.selfupdate()


    def finish_round(self):

        # Get surrender-ers
        cowards = Player.query(
            Player.sync == 3,
            ancestor=self.key).fetch(self.p_cur)

        # Sort out the rest
        others = Player.query(
            Player.sync == 2,
            ancestor=self.key).fetch(self.p_cur)

        winners = set()
        losers = set()

        maxhand = 0
        for player in others:
            hand_val = player.hand_val()

            if hand_val > 21 or hand_val < maxhand:
                losers.add(player)

            elif hand_val > maxhand:
                losers.update(winners)
                winners = {player}
                maxhand += 1

            else:
                winners.add(player)

        # Mark the game as finished
        self.playing = False
        # Save the game
        self.put()

        # Finish up with the players
        players = cowards + others
        for p in players:

            if p in cowards:
                p.tokens = int(p.wager/2)

            if p in winners:
                p.tokens = self.winnings()

            p.sync = 4

        ndb.put_multi(players)


    def notify_players(self):
        pass



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
            player = Player.get_by_id(pid)

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
