"""
this implements rotate-to-right and rotate-to-left to Tree object.
Unlike English, CCG categories are assigned to each punctuation in Japanese,
so punctuation rules (implemented in Rotating-CCG) are not necessary.
"""

from typing import Dict, Optional

from depccg.tree import Tree

# Japanese combinatory rules in ja.py
# forward_application,
# backward_application,
# forward_composition,
# generalized_backward_composition1,
# generalized_backward_composition2,
# generalized_backward_composition3,
# generalized_backward_composition4,
# generalized_forward_composition1,
# generalized_forward_composition2,
# generalized_forward_composition3,
# conjoin

class ApplyRightToLeft(object):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.fa = '>'
        self.ba = '<'
        self.fc = '>B'
        self.bc1 = '<B1'
        self.bc2 = '<B2'
        self.bc3 = '<B3'
        self.bc4 = '<B4'
        self.gfc1 = '>Bx1'
        self.gfc2 = '>Bx2'
        self.gfc3 = '>Bx3'
        self.order_dict: Dict[str, int] = {
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
    
    def toLeftBranching(self, node: Tree) -> Tree:
        if node.is_leaf:
            return node
        elif node.is_unary:
            return Tree.make_unary(node.cat,
                                   self.toLeftBranching(node.child),
                                   node.op_string,
                                   node.op_symbol)
        else:  # if node is binary
            return self.sinkForwardLeftward(Tree.make_binary(node.cat,
                                                        self.toLeftBranching(node.left_child),
                                                        self.toLeftBranching(node.right_child),
                                                        node.op_string,
                                                        node.op_symbol))
    
    def rebuild(self, combinatorOrder: int, node: Tree) -> Optional[Tree]:
        match node:
            case 
        
        if node.is_unary == False:
            if combinatorOrder >= self.order_dict[node.op_symbol]:
                
        else:
            return None
            
    def sinkForwardLeftward(self, node: Tree) -> Tree:
        
        



