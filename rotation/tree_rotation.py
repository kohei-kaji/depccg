"""
- This implements rotate-to-left to Tree object.
- Unlike English, CCG categories are assigned to each punctuation in Japanese,
  so special punctuation rules are not necessary.
"""

import argparse
from pathlib import Path
from typing import Dict, Optional

from depccg.cat import Category, Functor
from depccg.tree import Tree
from depccg.unification import Unification
from depccg.printer.ja import ja_of

from parsed_reader import read_parsedtree
from clear_features import clear_features

"""
All the original combinators in the Japanese CCGBank are follows;
  >, >B, >Bx1, >Bx2, >Bx3,
  <, <B1, <B2, <B3, <B4,
  ADV0, ADV1, ADV2,
  ADNint, ADNext, SSEQ
"""

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
            2: 'fc2',
            3: 'fc3'
}

order_to_forwardsymbol: Dict[int, str] = {
            0: '>',
            1: '>B',
            2: '>B2',
            3: '>B3'
}

order_to_forwardcrossedstring: Dict[int, str] = {
            1: 'fx',
            2: 'fx',
            3: 'fx',
            4: 'fx'
}

order_to_forwardcrossedsymbol: Dict[int, str] = {
            1: '>Bx1',
            2: '>Bx2',
            3: '>Bx3',
            4: '>Bx4'
}

order_to_backwardstring: Dict[int, str] = {
            0: 'ba',
            1: 'bx',
            2: 'bx',
            3: 'bx',
            4: 'bx',
}

order_to_backwardsymbol: Dict[int, str] = {
            0: '<',
            1: '<B1',
            2: '<B2',
            3: '<B3',
            4: '<B4',
}

def forward(cat_symbol: str) -> bool:
    return cat_symbol.startswith('>')

def backward(cat_symbol: str) -> bool:
    return cat_symbol.startswith('<')

def crossed(cat_symbol: str) -> bool:
    return 'x' in cat_symbol

def post_modifier(cat: Category) -> bool:
    return cat.is_functor and cat.left == cat.right and cat.slash == '\\'

def unification(cat_symbol: str):
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


######################################################################
#
#       >B[x]                          >B[y]
#       /  \         (if x ≥ y)         /  \
#      a   >B[y]        =>       >B[x-y+1] c
#          /  \                      /  \
#         b    c                    a    b
#
#
#       <B[x]                      <B[x+y-1]
#       /  \         (if y ≥ 1)       /  \
#      a   <B[y]        =>        <B[x]   c
#          /  \                    /  \
#         b    c                  a    b
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
######################################################################


# Rotate-to-left are implemented in post-order (bottom-up) traversal.
def toLeftward(top: Tree) -> Tree:
    if top.is_unary == False:
        a = top.left_child
        right = top.right_child
        def rebuild(x: int, r: Tree) -> Optional[Tree]:
            if r.is_unary == False and r.op_symbol != 'SSEQ':  # if node is binary and is not conjunction,
                y = cat_to_order[r.op_symbol]
                b, c = r.children
                if forward(top.op_symbol) and forward(r.op_symbol) and x >= y:
                    new_leftorder = x-y+1
                    new_toporder = y
                    newleft = rebuild(new_leftorder, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                r.op_string,
                                                r.op_symbol)
                    elif newleft == None:
                        if crossed(top.op_symbol) or crossed(r.op_symbol):
                            unification(order_to_forwardcrossedsymbol[new_leftorder])
                            if uni(clear_features(a.cat), b.cat):
                                newleft_cat = Functor(a.cat.left, "/", uni["c"])
                                newleft_string = order_to_forwardstring[new_leftorder]
                                newleft_symbol = order_to_forwardsymbol[new_leftorder]
                                unification(order_to_forwardcrossedsymbol[new_toporder])
                                if uni(newleft_cat, c.cat):
                                    newtop_cat = Functor(newleft_cat.left, "\\", uni["c"])
                                    return Tree.make_binary(newtop_cat,
                                                            Tree.make_binary(newleft_cat,
                                                                            a,
                                                                            b,
                                                                            newleft_string,
                                                                            newleft_symbol),
                                                            c,
                                                            order_to_forwardcrossedstring[new_toporder],
                                                            order_to_forwardcrossedsymbol[new_toporder])
                                else:
                                    return None
                            else:
                                return None
                        else:
                            unification(order_to_forwardsymbol[new_leftorder])
                            uni(clear_features(a.cat), b.cat)
                            newleft_cat = Functor(a.cat.left, "/", uni["c"])
                            newleft_string = order_to_forwardstring[new_leftorder]
                            newleft_symbol = order_to_forwardsymbol[new_leftorder]
                            unification(order_to_forwardsymbol[new_toporder])
                            if new_toporder >= 1:
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
                                    return None
                            else:
                                if uni(newleft_cat, c.cat):
                                    newtop_cat = uni["a"]
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
                                    return None
                    else:
                        return None
                elif backward(top.op_symbol) and backward(r.op_symbol) and y >= 1:
                    new_leftorder = x
                    new_toporder = x+y-1
                    newleft = rebuild(new_leftorder, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                r.op_string,
                                                r.op_symbol)
                    elif newleft == None:
                        unification(order_to_backwardsymbol[new_leftorder])
                        if uni(clear_features(a.cat), b.cat):
                            newleft_cat = Functor(a.cat.left, "\\", uni["c"])
                            newleft_string = order_to_backwardstring[new_leftorder]
                            newleft_symbol = order_to_backwardsymbol[new_leftorder]
                            unification(order_to_backwardsymbol[new_toporder])
                            if uni(newleft_cat, c.cat):
                                newtop_cat = Functor(newleft_cat.left, "\\", uni["c"])
                                return Tree.make_binary(newtop_cat,
                                                        Tree.make_binary(newleft_cat,
                                                                        a,
                                                                        b,
                                                                        newleft_string,
                                                                        newleft_symbol),
                                                        c,
                                                        order_to_backwardstring[new_toporder],
                                                        order_to_backwardsymbol[new_toporder])
                            else:
                                return None
                        else:
                            return None
                    else:
                        return None
                # elif forward(top.op_symbol) and backward(r.op_symbol) and post_modifier(c):
                #     if crossed(top.op_symbol):
                #         new_leftorder = y
                #         new_toporder = x+y-1
                #         newleft = rebuild(new_leftorder, b)
                #         if isinstance(newleft, Tree):
                #             return Tree.make_binary(top.cat,
                #                                     newleft,
                #                                     c,
                #                                     r.op_string,
                #                                     r.op_symbol)
                #         elif newleft == None:
                #             unification(order_to_backwardsymbol[new_leftorder])
                #             if uni(clear_features(a.cat), b.cat):
                #                 newleft_cat = Functor(a.cat.left, "\\", uni["c"])
                #                 newleft_string = order_to_backwardstring[new_leftorder]
                #                 newleft_symbol = order_to_backwardsymbol[new_leftorder]
                #                 unification(order_to_backwardsymbol[new_toporder])
                #                 if uni(newleft_cat, c.cat):
                #                     newtop_cat = Functor(newleft_cat.left, "\\", uni["c"])
                #                     return Tree.make_binary(newtop_cat,
                #                                             Tree.make_binary(newleft_cat,
                #                                                             a,
                #                                                             b,
                #                                                             newleft_string,
                #                                                             newleft_symbol),
                #                                             c,
                #                                             order_to_backwardstring[new_toporder],
                #                                             order_to_backwardsymbol[new_toporder])
                #                 else:
                #                     return None
                #             else:
                #                 return None
                #         else:
                #             return None
                #     else:



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
