import re
import argparse
from typing import Dict
from pathlib import Path

from depccg.cat import Category, Atom, Functor
from depccg.tree import Tree
from depccg.unification import Unification
from depccg.printer.ja import ja_of

from reader import read_parsedtree
from clear_features import clear_features

# When following verbs appear on the right of NPs, type-raise will be applied.
one_arg: Functor = Category.parse(r"S/(S\NP)")
two_args: Functor = Category.parse(r"(S\NP)/((S\NP)\NP)")
three_args: Functor = Category.parse(r"((S\NP)\NP)/(((S\NP)\NP)\NP)")
four_args: Functor = Category.parse(r"(((S\NP)\NP)\NP)/((((S\NP)\NP)\NP)\NP)")

def typeraise(r:Functor) -> Functor:
    vp = clear_features(r)
    match vp:
        case one_arg.right:
            return one_arg
        case two_args.right:
            return two_args
        case three_args.right:
            return three_args
        case four_args.right:
            return four_args
        case _:
            raise Exception('The category is not assumed to be inputted.')


class ApplyTypeRaise(object):
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        # self.tr_rules: Dict[str, str] = {}  # Dict[right-node, type-raised left-node]
    
    ####################################################
    # - For rule-based type-raise with ternary features
    #   - Now, features are ignored when type-raising.
    ####################################################
    
    # def readdict(self, dictpath: str = '/Users/kako/depccg/rotation/trdict.txt'):
    #     with open(dictpath, 'r') as f:
    #         for line in f:
    #             line = line.split()
    #             self.tr_rules[line[0]] = line[1]
    #     return self.tr_rules
    
    # def typeraise(self, x: Atom, y:Functor) -> Functor:
    #     uni = Unification("a/b", "b")
    #     tr: Functor = Category.parse(self.tr_rules[str(y)])
    #     if uni(tr, y):
    #         return tr
    #     else:
    #         raise Exception


    @staticmethod
    def apply_typeraise(tree: Tree) -> Tree:
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
                                            Tree.make_unary(typeraise(node.right_child.cat),
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
        # self.readdict()
        
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
  
