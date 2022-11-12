import re
from typing import Set, List

from depccg.cat import Category, Functor
from depccg.tree import Tree
from depccg.unification import Unification

def is_pure_forward(cat_symbol: str) -> bool:
    return cat_symbol.startswith('>') and 'x' not in cat_symbol

def is_forward(cat_symbol: str) -> bool:
    return cat_symbol.startswith('>')

def is_backward(cat_symbol: str) -> bool:
    return cat_symbol.startswith('<')

def is_crossed(cat_symbol: str) -> bool:
    return 'x' in cat_symbol

def is_modifier(cat: Category) -> bool:
    return cat.is_functor and cat.left == cat.right and cat.slash == '/'

def is_post_modifier(cat: Category) -> bool:
    return cat.is_functor and cat.left == cat.right and cat.slash == '\\'

def most_left_cat(cat: Category) -> str:
    s = str(cat)
    if re.match(r'\(*S', s) is not None:
        return 'S'
    else:
        return 'NP'

def is_vp(cat: Category) -> bool:
    """
    A functor category is a VP when
        1. it includes just one 'S' category and
        2. it starts with 'S' category and
        3. it has no forward slash ('/') in Japanese.
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

def tokens(tree: Tree) -> str:
    def rec(node: Tree):
        if node.is_leaf:
            result.append(node.children[0]['word'])
        else:
            for child in node.children:
                rec(child)
    result = []
    rec(tree)
    return ''.join(result)

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

# On the assumption that there is no backward function application (<), an l (left) category is always a complex category.
def can_combine(l: Functor, r: Category) -> bool:
    assert l.is_functor, "l must be a complex category."
    match l.slash:
        case '/':
            if l.right.is_atomic:
                return str(l.right) == most_left_cat(r)
            else:
                if r.is_atomic:
                    return l.right == r
                else:
                    return l.right == r.left
        case '\\':
            if r.is_atomic:
                return False
            else:
                if r.slash == '/':
                    return False
                else:
                    return l.left == r.right

# obtain the nodes in a left- or right-spine position in bottom-up traversal
class LeftSpine(object):
    def __init__(self):
        self.leftspine_list = []
    def traverse(self, node: Tree) -> None:
        if node.is_leaf == False:
            children = node.children
            if len(children) == 1:
                self.traverse(children[0])
                self.leftspine_list.append(node.cat)
            else:
                self.traverse(children[0])
                self.leftspine_list.append(node.cat)
        else:
            self.leftspine_list.append(node.cat)

    @staticmethod
    def output(tree: Tree) -> List[Category]:
        self = LeftSpine()
        self.traverse(tree)
        return self.leftspine_list

class RightSpine(object):
    def __init__(self):
        self.rightspine_list = []
    def traverse(self, node: Tree) -> None:
        if node.is_leaf == False:
            children = node.children
            if len(children) == 1:
                self.traverse(children[0])
                self.rightspine_list.append(node.cat)
            else:
                self.traverse(children[1])
                self.rightspine_list.append(node.cat)
        else:
            self.rightspine_list.append(node.cat)

    @staticmethod
    def output(tree: Tree) -> List[Category]:
        self = RightSpine()
        self.traverse(tree)
        return self.rightspine_list
