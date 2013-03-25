import logging
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
        
        myid = int(self.key.id() - self.deck().start_card)
        
        # First get suit
        if myid < 13:
            suit = 'h'
        elif myid < 26:
            suit = 'd'
            myid = myid - 13
        elif myid < 39:
            suit = 's'
            myid = myid - 26
        else:
            suit = 'c'
            myid = myid - 39

        # Then get number
        if myid is 0:
            val = 'A'
        elif myid < 10:
            val = str(myid-1)
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
    wager = ndb.IntegerProperty()
    cards_vis = ndb.KeyProperty(repeated=True)
    cards_inv = ndb.KeyProperty(repeated=True)
    cards_spl = ndb.KeyProperty(repeated=True)

    # Sync values:
    #   0 => Player has not yet taken any action
    #   1 => Player has acted, but is not standing
    #   2 => Player is standing
    #   3 => Player has surrendered
    #   4 => Player has joined game but is not playing
    sync = ndb.IntegerProperty(default=4)


    def game(self):
        
        return self.key.parent().get()


    def gamestatus_as_dict(self):

        cvis = [card.get().as_cardstr() for card in self.cards_vis]
        cinv = [card.get().as_cardstr() for card in self.cards_inv]

        return {'actions': self.actions(),
                'your_cards_visible': cvis,
                'common_cards_visible': [],
                'players': self.game().players_as_dict()}


    def info_as_dict(self):

        cvis = [card.get().as_cardstr() for card in self.cards_vis]
        cinv = [card.get().as_cardstr() for card in self.cards_inv]

        return {'name': self.name,
                'id': self.key.id(),
                'tokens': self.tokens,
                'avatar_url': self.a_url,
                'cards_visible': cvis,
                'cards_not_visible': cinv}


    def hand_values(self):

        values = {0}

        for card in self.cards_vis:
            values = {a+b for a in card.get().map_value() for b in values}

        return values


    def actions(self):

        if self.sync < 2 and self.game().playing:
            ret = ['hit',
                   'stand',
                   'doubledown']

            if self.sync is 0:
                ret.append('surrender')

                if self.cards_vis[0] is self.cards_vis[1]:
                    ret.append('split')

            return ret

        elif self.sync is 4:
            return ['join']
        else:
            return []


    def do_action(self, act, val):

        if act not in self.actions():
            return

        dispatch = getattr(self, '_{}'.format(act))
        dispatch(val)
        if self.sync is 0 and self.game().playing:
            self.sync = 1
        self.put()

        self.game().selfupdate()


    def _hit(self, val):
        gkey = self.key.parent()
        deck = Deck.query(ancestor=gkey).get()
        card = deck.draw()

        # Add card to hand
        self.cards_vis.append(card.key)


    def _stand(self, val):
        self.sync = 2


    def _doubledown(self, val):

        # Double your wager
        self.wager += self.wager

        # Take a single card
        self._hit(val)

        # And stand
        self._stand(val)


    def _split(self, val):

        # Set up the two different decks
        self.cards_spl.append(self.cards_vis.pop())


    def _surrender(self, val):

        # Mark self as surrendered
        self.sync = 3


    def _join(self, val):

        wager = int(val)

        # Submit bet
        self.wager = wager
        self.tokens -= wager

        # Get two cards
        self._hit(val)
        self._hit(val)

        # Set proper sync value
        self.sync = 0



class Game(ndb.Model):

    name = ndb.StringProperty(required=True)
    p_max = ndb.IntegerProperty(default=5)
    p_cur = ndb.IntegerProperty(default=0)
    playing = ndb.BooleanProperty(default=False)


    @classmethod
    def new(self, gid, name, p_max):
        oldgame = Game.get_by_id(gid)
        if oldgame:
            return oldgame.key

        new_game = Game(id=gid,
                        name = name,
                        p_max = p_max,
                        p_cur = 0,
                        playing = False)
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

        # Check if the round should start
        if self.playing:
            players = Player.query(Player.sync > 1, ancestor=self.key)
            if players.count(self.p_cur) is self.p_cur:
                self.finish_round()

        # Check if the round is done
        else:
            players = Player.query(Player.sync == 0, ancestor=self.key)
            if players.count(self.p_cur) is self.p_cur is not 0:
                self.start_round()

        # Send notification messages to connected clients
        self.notify_players()


    def start_round(self):

        self.playing = True
        self.put()


    def finish_round(self):

        # Get surrender-ers
        cowards = Player.query(
            Player.sync == 3,
            ancestor=self.key).fetch(self.p_cur)

        # Sort out the rest
        others = Player.query(
            Player.sync == 2,
            ancestor=self.key).fetch(self.p_cur)

        winners = []
        losers = []

        maxhand = 0
        for player in others:
            hand_val = player.hand_values()
            logging.info('{}\'s hand value: {}'.format(player.name, str(hand_val)))

            if all(v > 21 or v < maxhand for v in hand_val):
                losers.append(player)

            elif all(v > maxhand for v in hand_val):
                losers += winners
                winners = [player]
                maxhand += 1

            else:
                winners.append(player)

        # Mark the game as finished
        self.playing = False
        # Save the game
        self.put()

        # Finish up with the players
        players = cowards + others
        for p in players:

            # Rewards
            if p in cowards:
                p.tokens += int(p.wager/2)
            if p in winners:
                p.tokens += self.winnings(p)

            # Reset sync, cards, and bets
            p.sync = 4
            p.wager = 0
            p.cards_vis = []
            p.cards_inv = []
            p.cards_spl = []

        ndb.put_multi(players)


    def winnings(self, player):
        return int(player.wager*1.5)


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
