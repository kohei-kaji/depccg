# - This implements rotate-to-left to Tree object.
# - Unlike English, CCG categories are assigned to each punctuation in Japanese,
#   so special punctuation rules are not necessary.

import re
import argparse
from pathlib import Path
from typing import Dict, Optional

from depccg.cat import Category, Functor
from depccg.tree import Tree
from depccg.unification import Unification
from depccg.printer.ja import ja_of

from parsed_reader import read_parsedtree
from clear_features import clear_features

# all the original combinators in the Japanese CCGBank
#   >, >B, >Bx1, >Bx2, >Bx3,
#   <, <B1, <B2, <B3, <B4,
#   ADV0, ADV1, ADV2,
#   ADNint, ADNext, SSEQ
cat_to_order: Dict[str, int] = {
            '>':0,
            '<':0,
            '>B':1,
            '<B1':1,
            '<B2':2,
            '<B3':3,
            '<B4':4,
            '>Bx1':1,
            '>Bx2':2,
            '>Bx3':3
}

order_to_forwardstring: Dict[int, str] = {
            0: 'fa',
            1: 'fc',
            2: 'fc2'
}

order_to_forwardsymbol: Dict[int, str] = {
            0: '>',
            1: '>B',
            2: '>B2'
}

order_to_backwardstring: Dict[int, str] = {
            0: 'ba',
}

order_to_backwardsymbol: Dict[int, str] = {
            0: 'ba',
}

def forward(cat_symbol: str) -> bool:
    return (cat_symbol.startswith('>')) and ('x' not in cat_symbol)

def backward(cat_symbol: str) -> bool:
    return (cat_symbol.startswith('<')) and ('x' not in cat_symbol)

def cross_forward(cat_symbol: str) -> bool:
    return (cat_symbol.startswith('>')) and ('x' in cat_symbol)

def cross_backward(cat_symbol: str) -> bool:
    return (cat_symbol.startswith('<')) and ('x' in cat_symbol)


def allmadeof(a: Category, b: Category, c: Category) -> bool:
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


######################################################################
#       >Bx                         >By
#       /  \      (if x ≥ y)        /  \
#      a   >By        =>      >B(x-y+1) c
#          /  \                   /  \
#         b    c                 a    b
#
# toLeftward :: [Tree(right-branch)] -> [Tree(left-branch)]
#   // implemented by top-down traversal
#
# rebuild :: [x: int] -> [>By(b,c): Tree] -> [Optional[Tree]]
#
#
#
# - Common rotation examples.
# (1)
#          >B0:S                                  　>B0:S
#        /       \                                /      \
#  S/(S\NP)    >B0:S\NP        =>      >B1:S/(S\NP\NP)   S\NP\NP
#             /       \                      /      \
#  (S\NP)/(S\NP\NP)  S\NP\NP           S/(S\NP)   (S\NP)/(S\NP\NP)
#
# (2)
#          >B0:NP                            >B0:NP
#        /       \                          /      \
#     NP/NP    >B0:NP          =>      >B1:NP/NP    NP
#             /       \                 /      \
#           NP/NP     NP             NP/NP    NP/NP
#
#
#
# - forward, backward混在型, crossed composition混じりは未対応
#   - crossed composition混じりが現れうるかについては未確認。
# (3)
#          >B0:NP                            <B0:NP
#         /      \                           /     \
#     NP/NP    <B0:NP        =>           >B0:NP   NP\NP
#             /      \                   /     \
#            NP     NP\NP              NP/NP    NP
#
# (4)
#          >B0:S                            <B0:S
#         /      \                         /     \
#       S/S    <B0:S        =>         >B0:S     S\S
#             /      \                 /     \
#            S       S\S             S/S      S
#
# (4)
#        >Bx1:S/NP                          >Bx1:S/NP
#        /       \                           /      \
#      S/S   >Bx1:S/NP          =>      >B1:S/NP   NP\NP
#             /       \                /      \
#           S/NP     NP\NP           S/S     S/NP
######################################################################


def toLeftward(top: Tree) -> Tree:
    if (top.is_unary == False) and (forward(top.op_symbol)):
        a = top.left_child
        right = top.right_child
        def rebuild(x: int, r: Tree) -> Optional[Tree]:
            if (r.is_unary == False) and (r.op_symbol != 'SSEQ'):  # if node is binary and is not conjunction,
                y = cat_to_order[r.op_symbol]
                b, c = r.children
                if (forward(r.op_symbol)) and (x >= y):
                    new_order = x-y+1
                    newleft = rebuild(new_order, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                r.op_string,
                                                r.op_symbol)
                    elif (newleft == None) and (new_order <= 2):
                        uni = Unification("a/b", "b/c")
                        if uni(clear_features(a.cat),
                               b.cat):  # ignore the features of a.cat in this momemt
                            newleft_cat = Functor(a.cat.left, "/", uni["c"])
                            newleft_string = order_to_forwardstring[new_order]
                            newleft_symbol = order_to_forwardsymbol[new_order]
                            uni = Unification("a/b", "b/c")
                            if uni(newleft_cat, c.cat):
                                newtop_cat = Functor(newleft_cat.left, "/", uni["c"])
                                return Tree.make_binary(newtop_cat,
                                                        Tree.make_binary(newleft_cat,
                                                                        a,
                                                                        b,
                                                                        newleft_string,
                                                                        newleft_symbol),
                                                        c,
                                                        r.op_string,
                                                        r.op_symbol)
                            else:
                                return Tree.make_binary(top.cat,
                                                        Tree.make_binary(newleft_cat,
                                                                        a,
                                                                        b,
                                                                        newleft_string,
                                                                        newleft_symbol),
                                                        c,
                                                        r.op_string,
                                                        r.op_symbol)
                        else:
                            return None
                    else:
                        return None

                elif (top.op_symbol == '>')\
                        and (r.op_symbol == '<')\
                            and allmadeof(a.cat, b.cat, c.cat):  # if three categories are made of the same category,
                    new_order = 0
                    newleft = rebuild(new_order, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                r.op_string,
                                                r.op_symbol)
                    elif newleft == None:
                        uni = Unification("a/b", "b")
                        if uni(clear_features(a.cat),
                                b.cat):
                            newleft_cat = a.cat.left
                            return Tree.make_binary(top.cat,
                                                        Tree.make_binary(newleft_cat,
                                                                        a,
                                                                        b,
                                                                        'fa',
                                                                        '>'),
                                                        c,
                                                        r.op_string,
                                                        r.op_symbol)
                    else:
                        return None
                else:
                    return None
            else:
                return None

        rebranch = rebuild(cat_to_order[top.op_symbol],
                           right)

        if isinstance(rebranch, Tree):
            return rebranch
        else:
            return top
    else:
        return top


class TreeRotation(object):
    def __init__(self, filepath: str):
        self.filepath = filepath

    @staticmethod
    def rotate(node: Tree) -> Tree:
        if node.is_leaf:
            return node
        elif node.is_unary:
            return Tree.make_unary(node.cat,
                                   TreeRotation.rotate(node.child),
                                   node.op_string,
                                   node.op_symbol)
        else:  # if node is binary
            return toLeftward(Tree.make_binary(node.cat,
                                                        TreeRotation.rotate(node.left_child),
                                                        TreeRotation.rotate(node.right_child),
                                                        node.op_string,
                                                        node.op_symbol))


    @staticmethod
    def create_rotated_tree(args):
        self = TreeRotation(args.PATH)

        parent = Path(self.filepath).parent
        textname = str(Path(self.filepath).stem) + '_leftbranched.txt'
        trees = [tree for _, _, tree in read_parsedtree(self.filepath)]
        with open(parent / textname, 'w') as f:
            for tree in trees:
                tree = self.rotate(tree)
                f.write(ja_of(tree))
                f.write('\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH',
                        type=Path,
                        help='path to the file of the type-raised Japanese CCG derivations')

    args = parser.parse_args()
    TreeRotation.create_rotated_tree(args)
