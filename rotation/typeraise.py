import re
import argparse
from typing import Dict
from pathlib import Path

from depccg.cat import Category, Atom, Functor
from depccg.tree import Tree
from depccg.unification import Unification
from depccg.printer.ja import ja_of

from reader import read_parsedtree

class ApplyTypeRaise(object):
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.tr_rules: Dict[str, str] = {}  # Dict[right-node, type-raised left-node]
    
    def readdict(self, dictpath: str = '/Users/kako/depccg/rotation/trdict.txt'):
        with open(dictpath, 'r') as f:
            for line in f:
                line = line.split()
                self.tr_rules[line[0]] = line[1]
        return self.tr_rules
    
    # X -> T/(T\X)
    def typeraise(self, x: Atom, y:Functor) -> Functor:
        # results = [result for result in self.tr_rules[x.base]
        # if Category.parse(result).right == y
        # and x == Category.parse(result).right.right]
        # return results[0]
        uni = Unification("a/b", "b")
        tr: Functor = Category.parse(self.tr_rules[str(y)])
        
        if uni(tr, y):
            return tr
        else:
            raise Exception


    def apply_typeraise(self, node: Tree) -> Tree:
        if node.is_leaf:
            return Tree.make_terminal(node.token, node.cat)
        elif node.is_unary:
            return Tree.make_unary(node.cat,
                                   self.apply_typeraise(node.child),
                                   node.op_string, node.op_symbol)
        elif node.left_child.cat.is_atomic and node.left_child.cat.base == 'NP' and node.right_child.cat.is_functor:
            s = str(node.right_child.cat)
            if re.match(r'(\(*)S', s) is not None and s.count('S') == 1:
                return Tree.make_binary(node.cat,
                                        Tree.make_unary(self.typeraise(node.left_child.cat,
                                                                       node.right_child.cat),
                                                        self.apply_typeraise(node.left_child),
                                                        'tr',
                                                        '>T'),
                                        self.apply_typeraise(node.right_child),
                                        'fa',
                                        '>')
            else:
                return Tree.make_binary(node.cat,
                                        self.apply_typeraise(node.left_child),
                                        self.apply_typeraise(node.right_child),
                                        node.op_string,
                                        node.op_symbol)
        else:
            return Tree.make_binary(node.cat,
                                    self.apply_typeraise(node.left_child),
                                    self.apply_typeraise(node.right_child),
                                    node.op_string,
                                    node.op_symbol)
    
    
        
    def _traverse(self, tree: Tree) -> None:
        if tree.is_leaf == False:
            if len(tree.children) == 1:
                self._traverse(tree.children[0])
            else:
                left, right = tree.children
                self._traverse(left)
                self._traverse(right)
                if left.cat.is_atomic and left.cat.base == 'NP' and right.cat.is_functor: # if left is NP and right is a functor
                    s = str(right.cat)
                    if re.match(r'(\(*)S', s) is not None and s.count('S') == 1:  # if right starts with S, that is, right is VP
                        
                        np_cat = left.cat
                        np_children = left.children
                        np_op_string = left.op_string
                        np_op_symbol = left.op_symbol
                        
                        tr_cat = self.typeraise(left.cat, right.cat)
                        tr_children = [Tree(np_cat, np_children, np_op_string, np_op_symbol)]                        
                        
                        tree.left_child.children = [Tree(np_cat, np_children, np_op_string, np_op_symbol)]
                        # tree.children = [Tree(tr_cat, [tree.left_child], 'tr', '>T'), right]
                        # tree = Tree(tree.cat, tree.children, 'fa', '>')
                        # tree.children = [Tree(tr_cat, tr_children, 'tr', '>T'), right]
                        # tree = Tree(tree.cat, tree.children, 'fa', '>')
                        # tree.op_string = 'fa'
                        # tree.op_symbol = '>'
                       
                        # tree = Tree(tree_cat, [tree_left, right], 'fa', '>')
                        # tree.children = [Tree(typeraise, origin_children, 'tr', '>T'), right]
                        # tree.left_child.children = origin_children
                        
                        # tree.left_child.children = np_children
                        # tree.children = [Tree(typeraise, origin_children, 'tr', '>T'), right]
                        # tree = Tree(tree_cat, [tree_left, right], 'fa', '>')

    @staticmethod
    def create_typeraised_tree(args):
        self = ApplyTypeRaise(args.PATH)
        self.readdict()
        
        parent = Path(self.filepath).parent
        textname = str(Path(self.filepath).stem) + '_typeraised'
        trees = [tree for _, _, tree in read_parsedtree(self.filepath)]
        with open(parent / textname, 'w') as f:
            for tree in trees:
                tree = self.apply_typeraise(tree)
                f.write(ja_of(tree))
                f.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH',
                        type=Path,
                        help='path to the file of the Japanese CCG derivations parsed by depccg')
    
    args = parser.parse_args()
    ApplyTypeRaise.create_typeraised_tree(args)
                        


#################################################
# 新たに導入するtype raising rule群
# 要検討
# 素性指定をするべきか否か。
# Atom.baseは、feature含めたstrでは？ -> 辞書はNPではなく、NP[case=ga, ...]で用意しなければ？
# forward type-raisingのみのdictにする。

# {key <- VP, value <- type-raised NP}
# tr_rules: Dict[str, str] = {
#     "S[mod=nm,form=da,fin=f]\NP[case=ga,mod=nm,fin=f]": "S[mod=X1,form=X2,fin=X3]/(S[mod=X1,form=X2,fin=X3]\NP[mod=X1,form=X2,fin=X3])",
#     }
