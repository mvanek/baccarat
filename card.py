from google.appengine.ext import ndb


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

class Card(ndb.Model):

    draws = ndb.IntegerProperty(default=0)


    def deck(self):

        return self.key.parent().get()


    def map_value(self):

        myid = (self.key.id() - self.deck().start_card) % 13
        return cval_map[myid%13]


    def as_cardstr(self):
        
        myid = int(self.key.id() - self.deck().start_card)
        return cstr_map[myid]
