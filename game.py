from google.appengine.ext import ndb
from player import Player
from deck import Deck

class Game(ndb.Model):

    name = ndb.StringProperty(required=True)
    deck = ndb.KeyProperty()
    playing = ndb.BooleanProperty(default=False)

    p_max = ndb.IntegerProperty(default=5)
    p_cur = ndb.IntegerProperty(default=0)
    dealer = ndb.KeyProperty()
    players = ndb.KeyProperty(repeated=True)


    @classmethod
    def new(self, gid, name, p_max):
        oldgame = Game.get_by_id(gid)
        if oldgame:
            return oldgame.key


        new_game = Game(id      = gid,
                        name    = name,
                        p_max   = p_max,
                        p_cur   = 1,
                        dealer  = None,
                        deck    = None,
                        playing = False)

        new_dealer = Player(id          = 'dealer',
                            name        = 'John Goodman, the Dealer',
                            tokens      = 0,
                            a_url       = '/static/img/dealer.png',
                            cards_vis   = [],
                            cards_inv   = [],
                            sync        = 0)

        new_game.players.append(new_dealer.key)
        new_game.dealer = new_dealer.key
        new_game.deck = Deck.new(1, new_game.key)

        new_dealer.put()
        new_game.put()

        return new_game.key


    def as_dict(self):

        return {'name': self.name,
                'id': self.key.id(),
                'players_max': self.p_max,
                'players_current': self.p_cur-1}


    def gamestatus_as_dict(self, player):

        return {
            'your_actions': player.actions(self),
            'your_cards_visible': [c.as_cardstr() for c in\
                    ndb.get_multi(player.cards_vis + player.cards_inv)],
            'common_cards_visible': [],
            'players': self.players_as_dict()
        }


    def players_as_dict(self):

        return [p.info_as_dict() for p in\
                   ndb.get_multi(self.players)]


    def players_sorted_by_sync(self):

        ret = (list(), list(), list(), list(), list())

        for p in ndb.get_multi(self.players)
            ret[p.sync].append(p)

        return ret


    def selfupdate(self):

        players_sorted = self.players_sorted_by_sync()

        # Check if the round is done
        if self.playing:
            players_ready = 0
            for i in range(2, 5):
                players_ready += len(players_sorted[i])
            if players_ready == self.p_cur:
                self.finish_round()

        # Check if the round should start
        else:
            players_ready = len(players_sorted[0])
            if players_ready == self.p_cur and self.p_cur > 1:
                self.start_round()

        # Send notification messages to connected clients
        self.notify_players()


    @ndb.transactional
    def start_round(self):

        self.playing = True

        # Get everyone
        dealer = self.dealer.get()
        deck = self.deck.get()
        players = ndb.get_multi(self.players)

        # Remove old cards from player hands, and if they're playing,
        # give them new ones
        anybody_playing = False
        for p in players:

            # Skip the dealer
            if p.key.id() == 'dealer':
                continue

            # Remove players' cards
            p.cards_vis = []
            p.cards_inv = []
            p.cards_spl = []

            # If the player is sitting out, set them as ready
            # for the round to end
            if p.wager is None:
                p.sync = 4

            # Give cards to those playing
            if p.sync == 0:
                anybody_playing = True
                p._hit(self)
                p._hit(self)

        # If nobody is actually playing, abort without changing the datastore
        if not anybody_playing:
            return

        # Give dealer cards
        dealer.cards_vis = []
        dealer.cards_inv = []
        dealer.cards_vis.append(deck.draw().key)
        dealer.cards_inv.append(deck.draw().key)
        dealer.sync = 4

        # Save game and players to datastore
        ndb.put_multi(players)
        self.put()


    @ndb.transactional
    def finish_round(self):

        players_sorted = self.players_sorted_by_sync()

        # Dealer plays
        dealer = self.dealer.get()
        dealer.cards_vis.append(dealer.cards_inv.pop())
        hand_vals = dealer.hand_values(dealer.cards_vis)
        while all(v < 19 or v > 21 for v in hand_vals) and\
                not all(v > 21 for v in hand_vals):
            dealer._hit(self)
            hand_vals = dealer.hand_values(dealer.cards_vis)

        # Get surrender-ers
        cowards = players_sorted[3]

        # Sort out the rest
        others = players_sorted[2]

        winners = []
        losers = []

        dealermax = 0
        dealerhand = self.dealer.get().hand_values()
        for v in dealerhand:
            if v < 22 and v > dealermax:
                dealermax = v

        for player in others:
            if player.key.id() == 'dealer':
                continue
            if any(v > dealermax and v < 22 for v in player.hand_values()):
                winners.append(player)
            else:
                losers.append(player)

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

        # Set the dealer as ready to play the next game
        dealer.sync = 0

        players.append(dealer)
        ndb.put_multi(players)


    def winnings(self, player):
        return int(player.wager*1.5)


    def notify_players(self):
        pass



