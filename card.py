from google.appengine.ext import ndb

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
