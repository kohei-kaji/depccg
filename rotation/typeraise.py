import argparse
from pathlib import Path

from depccg.cat import Category, Functor
from depccg.tree import Tree
from depccg.unification import Unification
from depccg.printer.ja import ja_of

from parsed_reader import read_parsedtree
from clear_features import clear_features


# Type-Raising is applied to the left-side category combined by backward application, such as
#     1. NPs combined with verbal phrases
#
#            NP             NP             (S\NP)\NP
#                    ------------------>T
#                    (S\NP)/((S\NP)\NP)
#                    -------------------------------->
#                                   S\NP
#         -------->T
#          S/(S\NP)
#         ------------------------------------------->
#                             S
#
#     2. or others
#
#           S        S\S
#         --->T
#         S/(S\S)
#         -------------->
#                S
#
#         NP/NP           NP            (NP/NP)\NP
#               -------------------->T
#               (NP/NP)/((NP/NP)\NP)
#               ---------------------------------->
#                             NP/NP
#         ----------------------------------------->B
#                             NP/NP


def typeraise(l: Category, r: Functor) -> Functor:
    l = clear_features(l)
    r = clear_features(r)
    return Functor(r.left, '/', Functor(r.left, '\\', l))


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
            elif node.op_symbol == '<':
                uni = Unification("a", "b\a")
                if uni(node.left_child.cat, node.right_child.cat):
                    return Tree.make_binary(node.cat,
                                            Tree.make_unary(typeraise(node.left_child.cat, node.right_child.cat),
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
