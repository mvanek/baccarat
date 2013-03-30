from google.appengine.ext import ndb
from card import Card
import random

class Deck(ndb.Model):

    num_decks = ndb.IntegerProperty()

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

        # Get all cards that haven't been drawn the max number of times
        cards = Card.query(Card.draws < self.num_decks,
                           ancestor=self.key).fetch(52)

        # If half the cards are gone, it's time to replace the deck.
        remaining_card_count = sum(self.num_decks - c.draws for c in cards)
        if remaining_card_count < self.num_decks*26:

            # Replace all Card entities with fresh ones.
            gid = self.key.parent().id()
            my_id = self.key.id()

            new_cards = [Card(key=ndb.Key('Game', gid,
                                          'Deck', my_id,
                                          'Card', i),
                              draws=0) for i in range(self.start_card,
                                                      self.start_card + 52)]
            ndb.put_multi(new_cards)

            # Now you can return any card
            cards = new_cards
                    .format(new_cards))

        # Return a random card.
        ret = random.choice(cards)
        ret.draws += 1
        ret.put()
        return ret

