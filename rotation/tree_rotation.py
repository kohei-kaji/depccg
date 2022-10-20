"""
- This implements rotate-to-left to Tree object.
- Unlike English, CCG categories are assigned to each punctuation in Japanese,
  so special punctuation rules are not necessary.
"""

import re
import logging
import argparse
from tqdm import tqdm
from pathlib import Path
from typing import Dict, Optional

from depccg.cat import Category, Functor
from depccg.tree import Tree
from depccg.types import CombinatorResult
from depccg.unification import Unification
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
from tools import (is_pure_forward,
                   is_backward,
                   is_modifier,
                   is_post_modifier)

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

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
            '>B2':2,
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
            2: 'fc'
}

order_to_forwardsymbol: Dict[int, str] = {
            0: '>',
            1: '>B',
            2: '>B2'
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

def unification(cat_symbol: str, left_cat: Category, right_cat: Category) -> Optional[CombinatorResult]:
    match cat_symbol:
        case '>':
            return forward_application(left_cat,right_cat)
        case '<':
            return backward_application(left_cat,right_cat)
        case '>B':
            return forward_composition(left_cat,right_cat)
        case '>B2':
            uni = Unification("a/b", "(b/c)|d")
            if uni(left_cat, right_cat):
                result = right_cat if is_modifier(left_cat) else left_cat.functor(
                    uni['a'] / uni['c'], uni['d'])
                return CombinatorResult(
                    cat=result,
                    op_string="fc",
                    op_symbol=">B2",
                    head_is_left=False,
                )
            return None
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
#   1. If a top-node and a right-node have a forward composition (not a crossed composition) or application:
#       >B[x]                          >B[y]
#       /  \        (if x ≥ y)          /  \
#      α   >B[y]        =>       >B[x-y+1]  γ
#          /  \                      /  \
#         β    γ                    α    β
#
#   2. If a top-node and a right-node have a backward composition or application:
#       <B[x]                      <B[x+y-1]
#       /  \        (if y ≥ 1)        /  \
#      α   <B[y]        =>        <B[x]   γ
#          /  \                    /  \
#         β    γ                  α    β
#
#   3. Else:  (If there is a modifier, a left-branch can also be made.)
#       3-1. If α is a modifier and γ is a post-modifier and they modify the same category:
#           >Bx[x]                       <B[x]
#           /  \                          /  \
#          α   <B[x]        =>        >Bx[x]   γ
#              /  \                    /  \
#             β    γ                  α    β
#
#       3-2. If α and β are modifiers and they modify the same category:
#           >Bx[x]                       >Bx[x]
#           /  \                          /  \
#          α   >Bx[x]        =>       >B[1]   γ
#              /  \                    /  \
#             β    γ                  α    β
#
#       3-3. If α is a modifier (and β and γ are combined by a forward application or a forward composition):
#          3-3-1.
#               >Bx[x]                       >B[0]
#               /  \                          /  \
#             α   >B[0]        =>       >Bx[x+1]   γ
#                  /  \                    /  \
#                 β    γ                  α    β
#          3-3-2.
#              >Bx[2]                        >B[1]
#               /  \                          /  \
#              α   >B[1]        =>       >Bx[2]   γ
#                  /  \                    /  \
#                 β    γ                  α    β
#
#       3-4. If γ is a post-modifier (and a top-node is constituted by a forward application):
#           >B[0]                        <B[0]
#           /  \                          /  \
#          α   <B[n]        =>        >B[0]   γ
#              /  \                    /  \
#             β    γ                  α    β
#
#           >B[0]                        <B[1]
#           /  \                          /  \
#          α   <B[n]        =>        >B[0]   γ
#              /  \                    /  \
#             β    γ                  α    β


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
                if is_pure_forward(top.op_symbol) and is_pure_forward(r.op_symbol) and x >= y:  # 1
                    new_leftorder = x-y+1
                    new_toporder = y
                    newleft = rebuild(new_leftorder, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                r.op_string,
                                                r.op_symbol)
                    else:
                        newleft_string = order_to_forwardstring[new_leftorder]
                        newleft_symbol = order_to_forwardsymbol[new_leftorder]
                        newleft_result = unification(newleft_symbol,a.cat,b.cat)
                        if isinstance(newleft_result, CombinatorResult):
                            newleft_cat = newleft_result.cat
                            newtop_result = unification(r.op_symbol,newleft_cat,c.cat)
                            if isinstance(newtop_result, CombinatorResult):
                                newtop_cat = newtop_result.cat
                                return Tree.make_binary(newtop_cat,
                                                        Tree.make_binary(newleft_cat,
                                                                        a,
                                                                        b,
                                                                        newleft_string,
                                                                        newleft_symbol),
                                                        c,
                                                        order_to_forwardstring[new_toporder],
                                                        order_to_forwardsymbol[new_toporder])
                            else:
                                return None
                        else:
                            return None
                elif is_backward(top.op_symbol) and is_backward(r.op_symbol) and y >= 1:  # 2
                    new_leftorder = x
                    new_toporder = x+y-1
                    newleft = rebuild(new_leftorder, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                order_to_backwardstring[new_leftorder],
                                                order_to_backwardsymbol[new_leftorder])
                    else:
                        newleft_string = order_to_backwardstring[new_leftorder]
                        newleft_symbol = order_to_backwardsymbol[new_leftorder]
                        newleft_result = unification(newleft_symbol,a.cat,b.cat)
                        if isinstance(newleft_result, CombinatorResult):
                            newleft_cat = newleft_result.cat
                            newtop_result = unification(order_to_backwardsymbol[new_toporder],newleft_cat,c.cat)
                            if isinstance(newtop_result, CombinatorResult):
                                newtop_cat = newtop_result.cat
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
                elif is_modifier(a.cat) and is_post_modifier(c.cat) and a.cat.right == c.cat.left:  # 3-1
                    new_leftorder = x
                    new_toporder = x
                    newleft = rebuild(new_leftorder, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                order_to_backwardstring[new_toporder],
                                                order_to_backwardsymbol[new_toporder])
                    else:
                        newleft_string = order_to_forwardcrossedstring[new_leftorder]
                        newleft_symbol = order_to_forwardcrossedsymbol[new_leftorder]
                        newleft_result = unification(newleft_symbol,a.cat,b.cat)
                        if isinstance(newleft_result, CombinatorResult):
                            newleft_cat = newleft_result.cat
                            newtop_result = unification(order_to_backwardsymbol[new_toporder],newleft_cat,c.cat)
                            if isinstance(newtop_result, CombinatorResult):
                                newtop_cat = newtop_result.cat
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
                elif is_modifier(a.cat) and is_modifier(b.cat) and a.cat.right == b.cat.left:  # 3-2
                    new_leftorder = 1
                    new_toporder = x
                    newleft = rebuild(new_leftorder, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                order_to_forwardcrossedstring[new_toporder],
                                                order_to_forwardcrossedsymbol[new_toporder])
                    else:
                        newleft_string = order_to_forwardstring[new_leftorder]
                        newleft_symbol = order_to_forwardsymbol[new_leftorder]
                        newleft_result = unification(newleft_symbol,a.cat,b.cat)
                        if isinstance(newleft_result, CombinatorResult):
                            newleft_cat = newleft_result.cat
                            newtop_result = unification(order_to_forwardcrossedsymbol[new_toporder],newleft_cat,c.cat)
                            if isinstance(newtop_result, CombinatorResult):
                                newtop_cat = newtop_result.cat
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
                elif is_modifier(a.cat) and r.op_symbol == '>':  # 3-3-1
                    new_leftorder = x-y+1
                    new_toporder = 0
                    newleft = rebuild(new_leftorder, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                order_to_forwardstring[new_toporder],
                                                order_to_forwardsymbol[new_toporder])
                    else:
                        newleft_string = order_to_forwardcrossedstring[new_leftorder]
                        newleft_symbol = order_to_forwardcrossedsymbol[new_leftorder]
                        newleft_result = unification(newleft_symbol,a.cat,b.cat)
                        if isinstance(newleft_result, CombinatorResult):
                            newleft_cat = newleft_result.cat
                            newtop_result = unification(order_to_forwardsymbol[new_toporder],newleft_cat,c.cat)
                            if isinstance(newtop_result, CombinatorResult):
                                newtop_cat = newtop_result.cat
                                return Tree.make_binary(newtop_cat,
                                                        Tree.make_binary(newleft_cat,
                                                                        a,
                                                                        b,
                                                                        newleft_string,
                                                                        newleft_symbol),
                                                        c,
                                                        order_to_forwardstring[new_toporder],
                                                        order_to_forwardsymbol[new_toporder])
                            else:
                                return None
                        else:
                            return None
                elif is_modifier(a.cat) and top.op_symbol == '>Bx2' and r.op_symbol == '>B':  # 3-3-2
                    new_leftorder = 2
                    new_toporder = 1
                    newleft = rebuild(new_leftorder, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                order_to_forwardstring[new_toporder],
                                                order_to_forwardsymbol[new_toporder])
                    else:
                        newleft_string = order_to_forwardcrossedstring[new_leftorder]
                        newleft_symbol = order_to_forwardcrossedsymbol[new_leftorder]
                        newleft_result = unification(newleft_symbol,a.cat,b.cat)
                        if isinstance(newleft_result, CombinatorResult):
                            newleft_cat = newleft_result.cat
                            newtop_result = unification(order_to_forwardsymbol[new_toporder],newleft_cat,c.cat)
                            if isinstance(newtop_result, CombinatorResult):
                                newtop_cat = newtop_result.cat
                                return Tree.make_binary(newtop_cat,
                                                        Tree.make_binary(newleft_cat,
                                                                        a,
                                                                        b,
                                                                        newleft_string,
                                                                        newleft_symbol),
                                                        c,
                                                        order_to_forwardstring[new_toporder],
                                                        order_to_forwardsymbol[new_toporder])
                            else:
                                return None
                        else:
                            return None
                elif is_post_modifier(c.cat) and top.op_symbol == '>' and a.cat.is_functor and a.cat.left.is_atomic:  # 3-4-1
                    new_leftorder = 0
                    new_toporder = 0
                    newleft = rebuild(new_leftorder, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                order_to_backwardstring[new_leftorder],
                                                order_to_backwardsymbol[new_leftorder])
                    else:
                        newleft_string = order_to_forwardstring[new_leftorder]
                        newleft_symbol = order_to_forwardsymbol[new_leftorder]
                        newleft_result = unification(newleft_symbol,a.cat,b.cat)
                        if isinstance(newleft_result, CombinatorResult):
                            newleft_cat = newleft_result.cat
                            newtop_result = unification(order_to_backwardsymbol[new_toporder],newleft_cat,c.cat)
                            if isinstance(newtop_result, CombinatorResult):
                                newtop_cat = newtop_result.cat
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
                        else: return None
                elif is_post_modifier(c.cat) and top.op_symbol == '>' and a.cat.is_functor and a.cat.left.is_functor:  # 3-4-2
                    new_leftorder = 0
                    new_toporder = 1
                    newleft = rebuild(new_leftorder, b)
                    if isinstance(newleft, Tree):
                        return Tree.make_binary(top.cat,
                                                newleft,
                                                c,
                                                order_to_backwardstring[new_leftorder],
                                                order_to_backwardsymbol[new_leftorder])
                    else:
                        newleft_string = order_to_forwardstring[new_leftorder]
                        newleft_symbol = order_to_forwardsymbol[new_leftorder]
                        newleft_result = unification(newleft_symbol,a.cat,b.cat)
                        if isinstance(newleft_result, CombinatorResult):
                            newleft_cat = newleft_result.cat
                            newtop_result = unification(order_to_backwardsymbol[new_toporder],newleft_cat,c.cat)
                            if isinstance(newtop_result, CombinatorResult):
                                newtop_cat = newtop_result.cat
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
                        else: return None
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

        trees = [tree for _, _, tree in tqdm(read_parsedtree(self.filepath))]
        OUTPUT_PATH = Path(self.filepath).parent / 'left.txt'
        with open(OUTPUT_PATH, 'w') as f:
            logger.info(f'writing to {f.name}')
            for tree in trees:
                tree = self.rotate(self.rotate(self.rotate(tree)))
                f.write(ja_of(tree))
                f.write('\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH',
                        type=Path,
                        help='path to the file of the type-raised Japanese CCG derivations')

    args = parser.parse_args()
    TreeRotation.create_rotated_tree(args)
