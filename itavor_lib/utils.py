class Choices(dict):
    """
    A dictionary which behaves like a tuple/list thingie
    for django choice lists.
    """
    def __new__(cls, *args):
        obj = super(Choices, cls).__new__(cls)
        if args:
            obj._orig = list(args[0])
            obj.update(enumerate(*args))
        return obj

    def __len__(self):
        return len(self._orig)

    def __iter__(self):
        return iter(self._orig)

    @property
    def default(self):
        """Default choice is the first key.
        """
        return self[0][0]

    def find(self, value, default=None):
        """Find they key for a verbose value (inverse lookup).
        """
        ind = [y for x,y in self].index(value)
        if ind == -1: return default
        return self._orig[ind][0]

    def index(self, value):
        """Given a key, value, or (key, value) tuple, find the index.
        """
        ind = [x for x,y in self].index(value)
        if ind == -1:
            ind = [y for x,y in self].index(value)
        if ind == -1:
            ind = self._orig.index(value)

        return ind
