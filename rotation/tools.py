import re
from typing import List, Set

from depccg.cat import Category
from depccg.tree import Tree
from depccg.unification import Unification


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

def madeof(cat: Category) -> Set[Category]:
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

def tokens(tree: Tree) -> List[str]:
    def rec(node: Tree):
        if node.is_leaf:
            result.append(node.children[0]['word'])
        else:
            for child in node.children:
                rec(child)
    result = []
    rec(tree)
    return result

def unification(cat_symbol: str) -> None:
    global uni
    match cat_symbol:
        case '>':
            uni = Unification("a/b", "b")
        case '<':
            uni = Unification("b", "a\\b")
        case '>B':
            uni = Unification("a/b", "b/c")
        case '>B2':
            uni = Unification("a/b", "(b/c)|d")
        case '>B3':
            uni = Unification("a/b", "((b/c)|d)|e")
        case '<B1':
            uni = Unification("b\\c", "a\\b")
        case '<B2':
            uni = Unification("(b\\c)|d", "a\\b")
        case '<B3':
            uni = Unification("((b\\c)|d)|e", "a\\b")
        case '<B4':
            uni = Unification("(((b\\c)|d)|e)|f", "a\\b")
        case '>Bx1':
            uni = Unification("a/b", "b\\c")
        case '>Bx2':
            uni = Unification("a/b", "(b\\c)|d")
        case '>Bx3':
            uni = Unification("a/b", "((b\\c)|d)|e")
        case '>Bx4':
            uni = Unification("a/b", "(((b\\c)|d)|e)|f")
