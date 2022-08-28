"""
this implements rotate-to-right and rotate-to-left to Tree object.
Unlike English, each punctuation is assgined category in Japanese,
so punctuation rules (implemented in Rotating-CCG) does not need to be take into account.
"""

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
    
    def forwardrighttoleft(self, node: Tree):
        pass
    
    def backwardrighttoleft(self, node: Tree):
        pass
    
    def traverse(self, node: Tree):
        pass



def toRightBranching(node: Tree) -> Tree:  # when tree is a LeftBranching
    
    """
    the Python re-implementation of 'toRightBranching' function defined in 
    Rotating-CCG/src/main/scala/edin/ccg/representation/transforms/Rebranching.scala
    
    each node is recursively mapped by 'sinkForwardRightward' funtion from bottom to up
    'toRightBranching' function works as a condition branch for 'sinkForwardRightward' funtion
    and 'sinkForwardRightward' funtion works as a 'rotate-to-right'
    """

    if node.is_unary() == False:  #node is a BinaryNode
        return sinkForwardRightward(
            node.op_symbol:str,
            toRightBranching(node.children[0]),
            toRightBranching(node.children[1])
        )
    elif node.is_leaf():  # a TerminalNode
        return node
    else:  # a NonTerminal and UnaryNode
        return sinkForwardRightward(
            node.op_symbol:str,
            toRightBranching(node.child())
        )

def toLeftBranchingSimplistic(node:Tree)->Tree:
    if node.is_unary() == False:  #node is a BinaryNode
        return sinkForwardLeftward(
            node.op_symbol:str,
            toLeftBranchingSimplistic(node.children[0]),
            toLeftBranchingSimplistic(node.children[1])
        )
    elif node.is_leaf():  # a TerminalNode
        return node
    else:  # a NonTerminal and UnaryNode
        return sinkForwardLeftward(
            node.op_symbol:str,
            toLeftBranchingSimplistic(node.child())
        )

def attachRightPuncAtBottom(node: Tree, punc: Tree) -> Tree:
    if node.is_leaf():  # TerminalNode
        return node.make_binary(node.cat(), node, punc, 'punc', RemovePunctuation(False))
    
        """
        method: make_binary(Args) -> Tree

        Args:
            cat: Category,
            left: 'Tree',
            right: 'Tree',
            op_string: str,
            op_symbol: str,
            head_is_left: bool = True
        """
    
    elif node.is_unary() == False:  # BinaryNode
        return node.make_binary(
            node.cat,
            node.left_child,
            attachRightPuncAtBottom(node.right_child, punc),
            node.op_string,
            node.op_symbol
            )
    else:  # NonTerminal and Unary
        return node.make_binary(
            node.cat,
            attachRightPuncAtBottom(node.child(), punc)
        )

def RemovePunctuation(punctuationIsLeft: bool) -> str:
    if punctuationIsLeft:
        return 'P<'
    else:
        return 'P>'

def sinkForwardRightward(node: Tree) -> Tree:
    # if node.is_leaf() and node.child.op_symbol() == RemovePunctuation(True):
    pass

def sinkForwardLeftward(node: Tree) -> Tree:
    pass
