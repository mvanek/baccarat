from google.appengine.ext import ndb
from player import Player
from deck import Deck

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



