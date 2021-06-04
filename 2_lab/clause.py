from literal import Literal

class Clause: 
    def __init__(self, literals, parents):
        self.literals = set(literals)
        self.parents = parents

    def __str__(self):
        return ' v '.join([str(literal) for literal in sorted(self.literals)])

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.__key() == other.__key()

    def __lt__(self, other):
        return len(self.literals) < len(other.literals) or \
        (len(self.literals) == len(other.literals) and self.__key() < other.__key())

    def __gt__(self, other):
        return len(self.literals) > len(other.literals) or \
        (len(self.literals) == len(other.literals) and self.__key() > other.__key())

    def __hash__(self):
        return hash(self.__key())

    def isRedundant(self, other):
        for c in other:
            if self != c and c.literals.issubset(self.literals): return True
        return False

    def isResolvable(self, other):
        for literal in self.literals: 
            if literal.negate() in other.literals: return True 
        return False 

    def negate(self):
        negations = set()
        [negations.add(Clause([l.negate()], None)) for l in self.literals]
        return negations

    def __key(self):
        return tuple(sorted(self.literals))

    def get_literals(self):
        return self.literals

    def get_parents(self):
        return self.parents