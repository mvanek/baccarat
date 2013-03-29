import logging
from google.appengine.ext import ndb
from player import Player
from deck import Deck

class Game(ndb.Model):

    name = ndb.StringProperty(required=True)
    p_max = ndb.IntegerProperty(default=5)
    p_cur = ndb.IntegerProperty(default=0)
    dealer = ndb.KeyProperty()
    deck = ndb.KeyProperty()
    playing = ndb.BooleanProperty(default=False)


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
                            parent      = new_game.key,
                            name        = 'John Goodman, the Dealer',
                            tokens      = 0,
                            a_url       = '/static/img/dealer.png',
                            cards_vis   = [],
                            cards_inv   = [],
                            sync        = 0)

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


    def players_as_dict(self):

        return Player.query(ancestor=self.key).map(
            lambda player: player.info_as_dict())


    def selfupdate(self):

        # Check if the round is done
        if self.playing:
            players = Player.query(Player.sync > 1, ancestor=self.key)
            if players.count(self.p_cur) == self.p_cur:
                self.finish_round()

        # Check if the round should start
        else:
            players = Player.query(Player.sync == 0, ancestor=self.key)
            if players.count(self.p_cur) == self.p_cur and self.p_cur > 1:
                self.start_round()

        # Send info to log
        logging.info('\n{}\n{}\n{}\n{}'.format(
            '*** Updating game status ***',
            '-->   Game running?: {}'.format(self.playing),
            '-->   Total Players: {}'.format(self.p_cur),
            '--> Players Waiting: {}'.format(players.count(self.p_cur))))

        # Send notification messages to connected clients
        self.notify_players()


    def start_round(self):

        self.playing = True

        dealer = self.dealer.get()
        deck = self.deck.get()

        dealer.cards_vis.append(deck.draw().key)
        dealer.cards_inv.append(deck.draw().key)
        dealer.sync = 4

        dealer.put()
        self.put()


    def finish_round(self):

        # Dealer plays
        dealer = self.dealer.get()

        dealer.cards_vis.append(dealer.cards_inv.pop())
        dealer.sync = 0

        hand_vals = dealer.hand_values(dealer.cards_vis)
        while all(v < 19 or v > 21 for v in hand_vals) and\
                not all(v > 21 for v in hand_vals):
            dealer._hit()
            hand_vals = dealer.hand_values(dealer.cards_vis)

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

        dealerhand = self.dealer.get().hand_values()
        dealermax = 0
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
            p.cards_vis = []
            p.cards_inv = []
            p.cards_spl = []

        dealer.cards_vis = []
        dealer.cards_inv = []

        players.append(dealer)
        ndb.put_multi(players)


        # Log results
        logging.info('\n{}\n{}\n{}\n{}'.format(
            '*** Finished game ***',
            '--> winners: {}'.format(map(
                lambda p: p.name, winners)),
            '-->  losers: {}'.format(map(
                lambda p: p.name, losers)),
            '--> cowards: {}'.format(map(
                lambda p: p.name, cowards))))


    def winnings(self, player):
        return int(player.wager*1.5)


    def notify_players(self):
        pass



