"""
- This implements rotate-to-left to Tree object.
- Unlike English, CCG categories are assigned to each punctuation in Japanese,
  so special punctuation rules are not necessary.
"""

import re
import argparse
from pathlib import Path
from typing import Dict, Optional

from depccg.cat import Category, Functor
from depccg.tree import Tree
from depccg.types import CombinatorResult
from depccg.printer.ja import ja_of
from depccg.grammar.ja import (forward_application,
                               backward_application,
                               forward_composition,
                               generalized_backward_composition1,
                               generalized_backward_composition2,
                               generalized_backward_composition3,
                               generalized_backward_composition4,
                               generalized_forward_composition1,
                               generalized_forward_composition2,
                               generalized_forward_composition3)

from parsed_reader import read_parsedtree

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
            1: 'fc'
}

order_to_forwardsymbol: Dict[int, str] = {
            0: '>',
            1: '>B'
}

order_to_forwardcrossedstring: Dict[int, str] = {
            1: 'fx',
            2: 'fx',
            3: 'fx'
}

order_to_forwardcrossedsymbol: Dict[int, str] = {
            1: '>Bx1',
            2: '>Bx2',
            3: '>Bx3'
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

def unification(cat_symbol: str, left_cat: Category, right_cat: Category) -> Optional[CombinatorResult]:
    match cat_symbol:
        case '>':
            return forward_application(left_cat,right_cat)
        case '<':
            return backward_application(left_cat,right_cat)
        case '>B':
            return forward_composition(left_cat,right_cat)
        case '<B1':
            return generalized_backward_composition1(left_cat,right_cat)
        case '<B2':
            return generalized_backward_composition2(left_cat,right_cat)
        case '<B3':
            return generalized_backward_composition3(left_cat,right_cat)
        case '<B4':
            return generalized_backward_composition4(left_cat,right_cat)
        case '>Bx1':
            return generalized_forward_composition1(left_cat,right_cat)
        case '>Bx2':
            return generalized_forward_composition2(left_cat,right_cat)
        case '>Bx3':
            return generalized_forward_composition3(left_cat,right_cat)

# The following rotations are implemented;
#   1. When top-node and right-node have a forward composition or application,
#       >B[x]                          >B[y]
#       /  \        (if x ≥ y)          /  \
#      a   >B[y]        =>       >B[x-y+1] c
#          /  \                      /  \
#         b    c                    a    b
#
#   2. When top-node and right-node have a backward composition or application,
#       <B[x]                      <B[x+y-1]
#       /  \        (if y ≥ 1)        /  \
#      a   <B[y]        =>        <B[x]   c
#          /  \                    /  \
#         b    c                  a    b
#
#   3. When c is a post-modifier,
#       3-1. When top-node has a forward application,
#         >B[0]                       <B[0]
#         /  \                        /  \
#        a   <B[_]      =>         >B[0]  c
#             /  \                 /  \
#            b    c               a    b
#
#       3-2. When top-node has a forward composition,
#         3-2-1. When a is a modifier,
#            >Bx[x]                       <B[y]
#             /  \                        /  \
#            a   <B[y]      =>        >Bx[x]  c
#                 /  \                 /  \
#                b    c               a    b
#
#         3-2-2. When a is not a modifier...
#             >B[x]                       <B[x]
#             /  \                        /  \
#            a   <B[y]      =>         >B[x]  c
#                 /  \                 /  \
#                b    c               a    b

# - Rotate-to-left are implemented in post-order (bottom-up) traversal.
#   - An input tree is assumed to have no features.
def toLeftward(top: Tree) -> Tree:
    if top.is_unary == False:
        a = top.left_child
        right = top.right_child
        def rebuild(x: int, r: Tree) -> Optional[Tree]:  # When a input tree does not satisfy rotation conditions, always returns 'None'.
            if r.is_unary == False and r.op_symbol != 'SSEQ':  # if node is binary and is not conjunction,
                y = cat_to_order[r.op_symbol]
                b, c = r.children
                if is_forward(top.op_symbol) and is_forward(r.op_symbol) and x >= y:
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
                        if is_crossed(top.op_symbol) or is_crossed(r.op_symbol):  # if top-node or right-node has crossed composition,
                            if new_toporder == 0:
                                unification(order_to_forwardcrossedsymbol[new_leftorder])
                                if uni(clear_features(a.cat), b.cat):
                                    newleft_cat = Functor(a.cat.left, "\\", uni["c"])
                                    newleft_string = order_to_forwardcrossedstring[new_leftorder]
                                    newleft_symbol = order_to_forwardcrossedsymbol[new_leftorder]
                                    unification('>')
                                    if uni(newleft_cat, c.cat):
                                        newtop_cat = uni["a"]
                                        return Tree.make_binary(newtop_cat,
                                                                Tree.make_binary(newleft_cat,
                                                                                a,
                                                                                b,
                                                                                newleft_string,
                                                                                newleft_symbol),
                                                                c,
                                                                'fa',
                                                                '>')
                                    else:
                                        return None
                                else:
                                    return None
                            else:
                                unification(order_to_forwardsymbol[new_leftorder])
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
                        else:  # if both nodes have no crossed composition,
                            unification(order_to_forwardsymbol[new_leftorder])
                            uni(clear_features(a.cat), b.cat)
                            newleft_cat = Functor(a.cat.left, "/", uni["c"])
                            newleft_string = order_to_forwardstring[new_leftorder]
                            newleft_symbol = order_to_forwardsymbol[new_leftorder]
                            unification(order_to_forwardsymbol[new_toporder])
                            if new_toporder >= 1:  # if new_top has a functional composition,
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
                            else:  # if new_top has a functional application,  ## >, >Bx2のようなパターンだが、x≥yを満たしていない
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
                elif is_backward(top.op_symbol) and is_backward(r.op_symbol) and y >= 1:
                    new_leftorder = x
                    new_toporder = x+y-1
                    newleft = rebuild(new_leftorder, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                order_to_backwardstring[new_leftorder],
                                                order_to_backwardsymbol[new_leftorder])
                    elif newleft == None:
                        unification(order_to_backwardsymbol[new_leftorder])
                        if uni(clear_features(a.cat), b.cat):
                            newleft_cat = Functor(a.cat.left, "\\", uni["c"])
                            unification(order_to_backwardsymbol[new_toporder])
                            if uni(newleft_cat, c.cat):
                                newtop_cat = Functor(newleft_cat.left, "\\", uni["c"])
                                return Tree.make_binary(newtop_cat,
                                                        Tree.make_binary(newleft_cat,
                                                                        a,
                                                                        b,
                                                                        order_to_backwardstring[new_leftorder],
                                                                        order_to_backwardsymbol[new_leftorder]),
                                                        c,
                                                        order_to_backwardstring[new_toporder],
                                                        order_to_backwardsymbol[new_toporder])
                            else:
                                return None
                        else:
                            return None
                    else:
                        return None

                elif is_forward(top.op_symbol) and is_backward(r.op_symbol) and is_post_modifier(c.cat):
                    if top.op_symbol == '>':  # if top-node has a forward functional application,
                        new_leftorder = 0
                        new_toporder = 0
                        newleft = rebuild(new_leftorder, b)
                        if isinstance(newleft, Tree):
                            return Tree.make_binary(top.cat,
                                                    newleft,
                                                    c,
                                                    'ba',
                                                    '<')
                        elif newleft == None:
                            unification('>')
                            if uni(clear_features(a.cat), b.cat):
                                newleft_cat = uni["a"]
                                unification('<')
                                if uni(newleft_cat, c.cat):
                                    newtop_cat = uni["b"]
                                    return Tree.make_binary(newtop_cat,
                                                            Tree.make_binary(newleft_cat,
                                                                            a,
                                                                            b,
                                                                            'fa',
                                                                            '>'),
                                                            c,
                                                            'ba',
                                                            '<')
                                else:
                                    return None
                            else:
                                return None
                        else:
                            return None
                    elif is_modifier(a.cat):
                        new_leftorder = x
                        new_toporder = y
                        if is_crossed(top.op_symbol):
                            newleft = rebuild(new_leftorder, b)
                            if isinstance(newleft, Tree):
                                return Tree.make_binary(top.cat,
                                                        newleft,
                                                        c,
                                                        r.op_string,
                                                        r.op_symbol)
                            elif newleft == None:
                                unification(order_to_forwardcrossedsymbol[new_leftorder])
                                if uni(clear_features(a.cat), b.cat):
                                    newleft_cat = Functor(a.cat.left, "\\", uni["c"])
                                    unification(order_to_backwardsymbol[new_toporder])
                                    if uni(newleft_cat, c.cat):
                                        newtop_cat = Functor(newleft_cat.left, "\\", uni["c"])
                                        return Tree.make_binary(newtop_cat,
                                                                Tree.make_binary(newleft_cat,
                                                                                a,
                                                                                b,
                                                                                order_to_forwardcrossedstring[new_leftorder],
                                                                                order_to_forwardcrossedsymbol[new_leftorder]),
                                                                c,
                                                                order_to_backwardstring[new_toporder],
                                                                order_to_backwardsymbol[new_toporder])
                                    else:
                                        return None
                                else:
                                    return None
                            else:
                                return None
                        else:
                            return None
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
        textname = str(Path(self.filepath).stem) + '_left.txt'
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
