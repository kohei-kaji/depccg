# $ python test_rotation.py /Users/kako/depccg/rotation/test_sentence

import re
import argparse
from typing import Dict
from pathlib import Path

from depccg.cat import Category, Atom, Functor
from depccg.tree import Tree
from depccg.unification import Unification
from depccg.printer.ja import ja_of

from parsed_reader import read_parsedtree

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


    def apply_typeraise(self, tree: Tree) -> Tree:
        def _apply_typeraise(node: Tree) -> Tree:
            if node.is_leaf:
                return Tree.make_terminal(node.token, node.cat)
            elif node.is_unary:
                return Tree.make_unary(node.cat,
                                    _apply_typeraise(node.child),
                                    node.op_string, node.op_symbol)
            elif node.left_child.cat.is_atomic and node.left_child.cat.base == 'NP' and node.right_child.cat.is_functor:
                s = str(node.right_child.cat)
                if re.match(r'(\(*)S', s) is not None and s.count('S') == 1:
                    return Tree.make_binary(node.cat,
                                            Tree.make_unary(self.typeraise(node.left_child.cat,
                                                                        node.right_child.cat),
                                                            _apply_typeraise(node.left_child),
                                                            'tr',
                                                            '>T'),
                                            _apply_typeraise(node.right_child),
                                            'fa',
                                            '>')
                else:
                    return Tree.make_binary(node.cat,
                                            _apply_typeraise(node.left_child),
                                            _apply_typeraise(node.right_child),
                                            node.op_string,
                                            node.op_symbol)
            else:
                return Tree.make_binary(node.cat,
                                        _apply_typeraise(node.left_child),
                                        _apply_typeraise(node.right_child),
                                        node.op_string,
                                        node.op_symbol)
        return _apply_typeraise(tree)

                        

    @staticmethod
    def create_typeraised_tree(args):
        self = ApplyTypeRaise(args.PATH)
        self.readdict()
        
        parent = Path(self.filepath).parent
        textname = str(Path(self.filepath).stem) + '_typeraised'
        trees = [self.apply_typeraise(tree) for _, _, tree in read_parsedtree(self.filepath)]
        tree1 = trees[0]
        tree2 = trees[1]
        print('top-down traversal')
        print('top')
        print(tree1.cat)
        print(tree1.op_symbol)
        print('tree1.children')
        print(tree1.children)
        print()
            
        print('S/(S\\NP)')
        print(tree1.left_child.cat)
        print(tree1.left_child.op_symbol)
        print()
        
        print('NP')
        print(tree1.left_child.left_child.cat)
        print(tree1.left_child.left_child.op_symbol)
        print()
        
        print('NP')
        print(tree1.left_child.left_child.left_child.cat)
        print(tree1.left_child.left_child.left_child.op_symbol)
        print()
        
        print('NP\\NP')
        print(tree1.left_child.left_child.right_child.cat)
        print(tree1.left_child.left_child.right_child.op_symbol)
        print()
        
        print('S\\NP')
        print(tree1.right_child.cat)
        print(tree1.right_child.op_symbol)
        print()
            
        print('(S\\NP)/(S\\NP\\NP)')
        print(tree1.right_child.left_child.cat)
        print(tree1.right_child.left_child.op_symbol)
        print()
        
        print('NP')
        print(tree1.right_child.left_child.child.cat)
        print(tree1.right_child.left_child.child.op_symbol)
        print()
        
        print('NP')
        print(tree1.right_child.left_child.child.left_child.cat)
        print(tree1.right_child.left_child.child.left_child.op_symbol)
        print()
        
        print('NP\\NP')
        print(tree1.right_child.left_child.child.right_child.cat)
        print(tree1.right_child.left_child.child.right_child.op_symbol)
        print()
            
        print('S\\NP\\NP')
        print(tree1.right_child.right_child.cat)
        print(tree1.right_child.right_child.op_symbol)
        print()
        
        print('S\\NP\\NP')
        print(tree1.right_child.right_child.left_child.cat)
        print(tree1.right_child.right_child.left_child.op_symbol)
        print()
        
        print('S\\S')
        print(tree1.right_child.right_child.right_child.cat)
        print(tree1.right_child.right_child.right_child.op_symbol)
        print()

        print('tree2')
        print('top')
        print(tree2.cat)
        print(tree2.op_symbol)
        print()
            
        print('S/(S\\NP)')
        print(tree2.left_child.cat)
        print(tree2.left_child.op_symbol)
        print()
        
        print('NP')
        print(tree2.left_child.left_child.cat)
        print(tree2.left_child.left_child.op_symbol)
        print()
        
        print('NP')
        print(tree2.left_child.left_child.left_child.cat)
        print(tree2.left_child.left_child.left_child.op_symbol)
        print()
        
        print('NP\\NP')
        print(tree2.left_child.left_child.right_child.cat)
        print(tree2.left_child.left_child.right_child.op_symbol)
        print()
            
        print('S\\NP')
        print(tree2.right_child.cat)
        print(tree2.right_child.op_symbol)
        print()
            
            


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH',
                        type=Path,
                        help='path to the file of the Japanese CCG derivations parsed by depccg')
    
    args = parser.parse_args()
    ApplyTypeRaise.create_typeraised_tree(args)
                        
