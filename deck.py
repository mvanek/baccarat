from google.appengine.ext import ndb
from card import Card

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



