import re
from depccg.cat import Category


def is_vp(cat: Category) -> bool:
    """
    A functor category is VP when
        1. it includes just one 'S' category and
        2. it starts with 'S' category and
        3. it has no forward slash ('/').
    """
    s = str(cat)
    return (cat.is_functor
            and s.count('S') == 1
            and re.match(r'\(*S', s) is not None
            and re.search(r'/', s) is None)

def madeof(cat: Category):
    s = set()
    def rec(c):
        if c.is_functor:
            rec(c.left)
            rec(c.right)
        else:
            s.add(c.base)
        return s
    return rec(cat)

def theSameCats(a: Category, b: Category, c: Category) -> bool:
    s = set()
    def rec(cat):
        if cat.is_functor:
            rec(cat.left)
            rec(cat.right)
        else:
            s.add(cat.base)
        return s
    union = rec(a).union(rec(b),rec(c))
    return len(union) == 1
