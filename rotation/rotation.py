# - This implements rotate-to-left to Tree object.
# - Unlike English, CCG categories are assigned to each punctuation in Japanese,
#   so special punctuation rules are not necessary.

import re
import argparse
from pathlib import Path
from typing import Dict, Optional

from depccg.cat import Category
from depccg.tree import Tree
from depccg.unification import Unification
from depccg.printer.ja import ja_of
from reader import read_parsedtree

# all the original combinators in the Japanese CCGBank
#   >, >B, >Bx1, >Bx2, >Bx3,
#   <, <B1, <B2, <B3, <B4,
#   ADV0, ADV1, ADV2, 
#   ADNint, ADNext, SSEQ

class TreeRotation(object):
    def __init__(self, filepath: str):
        self.filepath = filepath
        
        self.cat_to_order: Dict[str, int] = {
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
        
        self.order_to_forwardstring: Dict[int, str] = {
            0: 'fa',
            1: 'fc',
            2: 'fc2'
        }
        
        self.order_to_forwardsymbol: Dict[int, str] = {
            0: '>',
            1: '>B',
            2: '>B2'
        }
        

    def forward(self, cat_symbol: str) -> bool:
        return (cat_symbol.startswith('>')) and ('x' not in cat_symbol)
    
    
    def rotate2left(self, node: Tree) -> Tree:
        if node.is_leaf:
            return node
        elif node.is_unary:
            return Tree.make_unary(node.cat,
                                   self.rotate2left(node.child),
                                   node.op_string,
                                   node.op_symbol)
        else:  # if node is binary
            return self.sinkForwardLeftward(Tree.make_binary(node.cat,
                                                        self.rotate2left(node.left_child),
                                                        self.rotate2left(node.right_child),
                                                        node.op_string,
                                                        node.op_symbol))



	######################################################################
    #       >Bx                         >By
    #       /  \      (if x ≥ y)        /  \
    #      a   >By        =>      >B(x-y+1) c
    #          /  \                   /  \
	#         b    c                 a    b
	#
    # sinkForwardLeftward :: [Tree(right-branch)] -> [Tree(left-branch)]
    #   // implemented from bottom to up
    #
    # rebuild :: [x: int] -> [>By(b,c): Tree] -> [Optional[Tree]]
    #
    #
    #
    #          >B0:S                                    >B0:S
    #        /       \                                /      \
    #  S/(S\NP)    >B0:S\NP        =>    >B1:S/((S\NP)\NP)   S\NP\NP
    #             /       \                      /      \
	#  (S\NP)/(S\NP\NP)  S\NP\NP           S/(S\NP)   (S\NP)/(S\NP\NP)
	#
    #
    #          >B0:NP                             >B0:NP
    #        /       \                           /      \
    #     NP/NP    >B0:NP          =>      >B1:NP/NP    NP
    #             /       \                 /      \
	#           NP/NP     NP             NP/NP    NP/NP
	######################################################################

    def sinkForwardLeftward(self, top: Tree) -> Tree:
        if top.is_unary == False:
            a = top.left_child
            right = top.right_child
            def rebuild(x: int, r: Tree) -> Optional[Tree]:
                if r.is_unary == False:  # if node is binary,
                    y = self.cat_to_order[r.op_symbol]
                    if (self.forward(r.op_symbol)) and (x >= y):  # if forward-rotate-to-left can be applied,
                        b, c = r.children
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
                            uni(a.cat, b.cat)
                            newl_cat = Category.parse(str(uni["a"]) + "/(" + str(uni["c"]) + ")")
                            newl_string = self.order_to_forwardstring[new_order]
                            newl_symbol = self.order_to_forwardsymbol[new_order]
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
                else:
                    return None
            rebranch = rebuild(self.cat_to_order[top.op_string],
                               right)
            
            if isinstance(rebranch, Tree):
                return rebranch
            else:
                return top
    
    @staticmethod
    def create_rotated_tree(args):
        self = TreeRotation(args.PATH)

        parent = Path(self.filepath).parent
        textname = str(Path(self.filepath).stem) + '_leftbranched'
        trees = [tree for _, _, tree in read_parsedtree(self.filepath)]
        with open(parent / textname, 'w') as f:
            for tree in trees:
                tree = self.rotate2left(tree)
                f.write(ja_of(tree))
                f.write('\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH',
                        type=Path,
                        help='path to the file of the type-raised Japanese CCG derivations')
    
    args = parser.parse_args()
    TreeRotation.create_rotated_tree(args)
