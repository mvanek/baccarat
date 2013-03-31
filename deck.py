from google.appengine.ext import ndb
from card import Card
import random


cval_map = [
    # Ace
    {1, 11},
    # Numbers
    {2}, {3}, {4}, {5},
    {6}, {7}, {8}, {9}, {10},
    # Face
    {10}, {10}, {10}]

cstr_map = [
    ## Hearts
        # Ace
        'Ah',
        # Numbers
        '2h', '3h', '4h', '5h',
        '6h', '7h', '8h', '9h', '10h',
        # Face
        'Jh', 'Qh', 'Kh',


    ## Diamonds
        # Ace
        'Ad',
        # Numbers
        '2d', '3d', '4d', '5d',
        '6d', '7d', '8d', '9d', '10d',
        # Face
        'Jd', 'Qd', 'Kd',

    ## Spades
        # Ace
        'As',
        # Numbers
        '2s', '3s', '4s', '5s',
        '6s', '7s', '8s', '9s', '10s',
        # Face
        'Js', 'Qs', 'Ks',

    ## Clubs
        # Ace
        'Ac',
        # Numbers
        '2c', '3c', '4c', '5c',
        '6c', '7c', '8c', '9c', '10c',
        # Face
        'Jc', 'Qc', 'Kc']

class Deck(ndb.Model):

    num_decks = ndb.IntegerProperty()
    cards = ndb.KeyProperty(repeated=True)

    @classmethod
    def new(self, num_decks, parent_key):

        new_deck = Deck(num_decks=num_decks, parent=parent_key)

        first, last = Card.allocate_ids(52)
        new_deck.cards = [ndb.Key('Card', k) for k in range(first, last+1)]

        ndb.put_multi([Card(key=k) for k in new_deck.cards])
        new_deck.put()

        return new_deck.key


    def sort_cards(self):

        all_cards = ndb.get_multi(self.cards)

        available_cards = []
        count = 0
        for card in all_cards:

            num_avail = self.num_decks - card.draws
            count += num_avail

            if num_avail > 0:
                available_cards.append(card)

        return count, available_cards


    def draw(self):

        remaining_count, cards = self.sort_cards()

        # If half the cards are gone, it's time to replace the deck.
        if remaining_count < self.num_decks*26:

            self.cards = [Card(k) for k in cards]

            # Now you can return any card
            ndb.put_multi(self.cards)
            self.put()

        # Return a random card. Note that we're returning a card from the old deck
        # even if we just refreshed it. Don't save the card because the deck is gone.
        ret = random.choice(cards)
        ret.draws += 1
        return ret


    def map_card_value(self, card_k):

        myid = (card_k.id() - self.cards[0].id()) % 13
        return cval_map[myid%13]


    def card_as_str(self, card_k):

        myid = int(card_k.id() - self.cards[0].id())
        return cstr_map[myid]
