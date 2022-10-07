import logging
import argparse
from pathlib import Path
from collections import defaultdict

from depccg.tools.ja.reader import read_ccgbank
from depccg.tree import Tree

from parsed_reader import read_parsedtree

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class CombinatorListCreator(object):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.combinator_list = defaultdict(int)

    def _traverse(self, tree: Tree):
        if tree.is_leaf == False:
            children = tree.children
            if len(children) == 1:
                self._traverse(children[0])
                self.combinator_list[tree.op_symbol] += 1
            else:
                self._traverse(children[0])
                self._traverse(children[1])
                self.combinator_list[tree.op_symbol] += 1

    @staticmethod
    def _write(dct, filename):
        with open(filename, 'w') as f:
            logger.info(f'writing to {f.name}')
            for key, value in dct.items():
                print(f'{key} # {str(value)}', file=f)

    @staticmethod
    def create_combinatorlist(args):
        self = CombinatorListCreator(args.PATH)

        trees = [tree for _, _, tree in read_ccgbank(self.filepath)]
        for tree in trees:
            self._traverse(tree)

        combinator_list = {f'{k}': v for k, v in self.combinator_list.items()}
        parent = Path(args.PATH).parent
        textname = str(Path(args.PATH).stem) + 'combinator_list'
        self._write(combinator_list, parent / textname)


class CombinatorPairFinder(object):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.combinatorPairList = []
        # self.combinatorPairWithUnaryList = []

    def _traverse(self, tree: Tree):
        if tree.is_leaf == False:
            children = tree.children
            if len(children) == 1:
                self._traverse(children[0])
            else:
                self._traverse(children[0])
                self._traverse(children[1])
                if children[1].is_unary == False:
                    self.combinatorPairList.append([tree.op_symbol,
                                                    children[1].op_symbol,
                                                    str(tree.cat),
                                                    str(children[1].left_child.cat),
                                                    str(children[1].right_child.cat)])

    @staticmethod
    def create_combinatorPairList(args):
        self = CombinatorPairFinder(args.PATH)

        trees = [tree for _, _, tree in read_parsedtree(self.filepath)]
        for tree in trees:
            self._traverse(tree)
        seen = []
        for i in self.combinatorPairList:
            if i not in seen:
                seen.append(i)
        seen.sort()

        parent = Path(args.PATH).parent
        textname = str(Path(args.PATH).stem) + 'combinators.txt'
        with open(parent/textname, 'w') as f:
            for i in seen:
                print(f'{i[0]}, {i[1]}; {i[2]}, {i[3]}, {i[4]}', file=f)


    # Unary ruleが入ったときの、
    #
    #           a
    #           |
    #           b
    #          / \
    #         c   d
    #
    #
    # def _traverseWithUnary(self, tree: Tree):
    #     if tree.is_leaf == False:
    #         children = tree.children
    #         if len(children) == 1:
    #             self._traverseWithUnary(children[0])
    #         else:
    #             self._traverseWithUnary(children[0])
    #             self._traverseWithUnary(children[1])
    #             if children[1].is_unary:
    #                 self._traverseWithUnary(children[0].right_child)
    #                 self._traverseWithUnary(children[0].left_child)

    # @staticmethod
    # def create_combinatorPairWithUnaryList(args):
    #     self = CombinatorPairFinder(args.PATH)

    #     trees = [tree for _, _, tree in read_parsedtree(self.filepath)]
    #     for tree in trees:
    #         self._traverse(tree)

    #     combinatorPairList = {f'{k}': v for k, v in self.combinatorPairList.items()}
    #     parent = Path(args.PATH).parent
    #     textname = str(Path(args.PATH).stem) + 'combinators.txt'
    #     self._write(combinatorPairList, parent / textname)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH',
                        type=Path,
                        help='path to JapaneseCCGBank data file')
    parser.add_argument('--input',
                        help="Choose 'uni' or 'pair'. The former outputs the all of the combinators in the input data, and the latter outputs the combinators of a top-node and right-child-node.",
                        choices=['uni', 'pair'],
                        default='uni')
    args = parser.parse_args()

    if args.input == 'pair':
        CombinatorPairFinder.create_combinatorPairList(args)
    else:
        CombinatorListCreator.create_combinatorlist(args)
