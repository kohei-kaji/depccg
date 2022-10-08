import logging
import argparse
from pathlib import Path
from collections import defaultdict

from depccg.tools.ja.reader import read_ccgbank
from depccg.printer.deriv import deriv_of
from depccg.tree import Tree

from parsed_reader import read_parsedtree, read_parsedstring

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
                                                    str(children[0].cat),
                                                    str(children[1].cat),
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
        stack = []
        with open(parent/textname, 'w') as f:
            for i in seen:
                print(f'op_symbol: {i[0]}, {i[1]}', file=f)
                #
                #             op_symbol: i[0], cat: i[2]
                #                  /              \
                #                 /                \
                #           cat: i[3]     op_symbol: i[1], cat: i[4]
                #                                /       \
                #                               /         \
                #                         cat: i[5]     cat: i[6]
                #
                stack.append('{' + i[0] + ' ' + i[2] + ' {' + i[3] + ' 1/1/_/_} {' + i[1] + ' ' + i[4] + ' {' + i[5] + ' 2/2/_/_} {' + i[6]+ ' 3/3/_/_}}}')
            f.write('\n')
            for i,j in enumerate(read_parsedstring(stack)):
                f.write(str(i))
                f.write('\n')
                f.write(deriv_of(j))
                f.write('\n')


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
