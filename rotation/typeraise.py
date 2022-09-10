import re
import argparse
from pathlib import Path

from depccg.cat import Category, Functor
from depccg.tree import Tree
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
            raise Exception('This category is not assumed to be inputted.')


class TypeRaise(object):
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath


    @staticmethod
    def apply_typeraise(tree: Tree) -> Tree:
        def _apply_typeraise(node: Tree) -> Tree:
            if node.is_leaf:
                return Tree.make_terminal(node.token, node.cat)
            elif node.is_unary:
                return Tree.make_unary(node.cat,
                                    _apply_typeraise(node.child),
                                    node.op_string, node.op_symbol)
            elif node.left_child.cat.is_atomic\
                and node.left_child.cat.base == 'NP'\
                    and node.right_child.cat.is_functor:
                s = str(node.right_child.cat)
                if s.count('S') == 1\
                    and re.match(r'(\(*)S', s) is not None:
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
        self = TypeRaise(args.PATH)

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
    TypeRaise.create_typeraised_tree(args)
