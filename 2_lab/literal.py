
class Literal:
    def __init__(self, name, neg):        
        self.name = name
        self.neg = neg

    def __str__(self):
        if self.neg: return '~' + self.name
        return self.name

    def __eq__(self, other):
        return self.__key() == other.__key()

    def __lt__(self, other):
        return self.__key() < other.__key()

    def __gt__(self, other):
        return self.__key() > other.__key()

    def __repr__(self):
        return self.__str__()

    def __key(self):
        return (self.name, self.neg)

    def __hash__(self):
        return hash(self.__key())

    def negate(self):
        return Literal(self.name, not self.neg)
    
