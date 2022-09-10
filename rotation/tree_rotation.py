# - This implements rotate-to-left to Tree object.
# - Unlike English, CCG categories are assigned to each punctuation in Japanese,
#   so special punctuation rules are not necessary.

import re
import argparse
from pathlib import Path
from typing import Dict, Optional

from depccg.cat import Functor
from depccg.tree import Tree
from depccg.unification import Unification
from depccg.printer.ja import ja_of

from reader import read_parsedtree
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
        

def forward(cat_symbol: str) -> bool:
    return (cat_symbol.startswith('>')) and ('x' not in cat_symbol)


def toLeftward(top: Tree) -> Tree:
    if (top.is_unary == False) and (forward(top.op_symbol)):
        a = top.left_child
        right = top.right_child
        def rebuild(x: int, r: Tree) -> Optional[Tree]:
            if r.is_unary == False:  # if node is binary,
                y = cat_to_order[r.op_symbol]
                b, c = r.children
                if (forward(r.op_symbol)) and (x >= y):
                    new_order = x-y+1
                    newl = rebuild(new_order, b)
                    if isinstance(newl, Tree):
                        return Tree.make_binary(top.cat,
                                                newl,
                                                c,
                                                r.op_string,
                                                r.op_symbol)
                    elif (newl == None) and (new_order <= 2):
                        uni = Unification("a/b", "b/c")
                        if uni(clear_features(a.cat),
                               b.cat):  # ignore the features of a.cat in this momemt
                            newl_cat = Functor(a.cat.left, "/", uni["c"])
                            newl_string = order_to_forwardstring[new_order]
                            newl_symbol = order_to_forwardsymbol[new_order]
                            return Tree.make_binary(top.cat,
                                                    Tree.make_binary(newl_cat,
                                                                    a,
                                                                    b,
                                                                    newl_string,
                                                                    newl_symbol),
                                                    c,
                                                    r.op_string,
                                                    r.op_symbol)
                        else:
                            return None
                    else:
                        return None
                    
                elif (top.op_symbol == '>')\
                        and (r.op_symbol == '<')\
                            and (a.cat.right.base == 'NP')\
                                    and (c.cat.right.is_atomic)\
                                        and (c.cat.right.base == 'NP')\
                                            and (re.match(r'(\(*)NP', str(b.cat)) is not None):
                    uni = Unification("a/b", "b")
                    if uni(clear_features(a.cat),
                               b.cat):
                        newl_cat = a.cat.left
                        return Tree.make_binary(top.cat,
                                                Tree.make_binary(newl_cat,
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

        rebranch = rebuild(cat_to_order[top.op_string],
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



    ######################################################################
    #       >Bx                         >By
    #       /  \      (if x ≥ y)        /  \
    #      a   >By        =>      >B(x-y+1) c
    #          /  \                   /  \
    #         b    c                 a    b
    #
    # toLeftward :: [Tree(right-branch)] -> [Tree(left-branch)]
    #   // implemented from bottom to up
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
    #        >Bx1:S/NP                          >Bx1:S/NP
    #        /       \                           /      \
    #      S/S   >Bx1:S/NP          =>      >B1:S/NP   NP\NP
    #             /       \                /      \
    #           S/NP     NP\NP           S/S     S/NP
    ######################################################################

    
    @staticmethod
    def create_rotated_tree(args):
        self = TreeRotation(args.PATH)

        parent = Path(self.filepath).parent
        textname = str(Path(self.filepath).stem) + '_leftbranched'
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
