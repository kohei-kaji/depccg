import logging
import argparse
from pathlib import Path
from re import T
from typing import List
from collections import defaultdict
from tqdm import tqdm

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
    def __init__(self, path_list: List[str]):
        self.filepath = path_list
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

        seen = []
        for path in self.pathlist:
            trees = [tree for _, _, tree in read_parsedtree(path)]
            for tree in trees:
                self._traverse(tree)
            for i in self.combinatorPairList:
                if i not in seen:
                    seen.append(i)
        return seen.sort()


    def write(self, args):
        parent = Path(args.PATH[0]).parent
        textname = 'combinators.txt'
        stack = []
        seen = self.create_combinatorPairList(args)
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


class RevealFinder(object):
    def __init__(self, path_list: List[str]):
        self.path_list = path_list
        self.revealList= []

    def _traverse(self, tree: Tree):
        if tree.is_leaf == False:
            if len(tree.children) == 1:
                self._traverse(tree.child)
            else:
                self._traverse(tree.left_child)
                self._traverse(tree.right_child)
                if tree.right_child.is_leaf == False:
                    if len(tree.right_child.children) == 1:
                       self._traverse(tree.right_child.child)
                    else:
                        self._traverse(tree.right_child.left_child)
                        self._traverse(tree.right_child.right_child)
                        if tree.right_child.left_child.is_leaf == False:
                            if len(tree.right_child.left_child.children) == 1:
                                self._traverse(tree.right_child.left_child.child)
                            else:
                                self._traverse(tree.right_child.left_child.left_child)
                                self._traverse(tree.right_child.left_child.right_child)
                                self.revealList.append([tree.op_symbol,
                                                        tree.right_child.op_symbol,
                                                        tree.right_child.left_child.op_symbol,
                                                        str(tree.cat),
                                                        str(tree.left_child.cat),
                                                        str(tree.right_child.cat),
                                                        str(tree.right_child.left_child.cat),
                                                        str(tree.right_child.right_child.cat),
                                                        str(tree.right_child.left_child.left_child.cat),
                                                        str(tree.right_child.left_child.right_child.cat)])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH',
                        nargs="*",
                        type=Path,
                        help='path to JapaneseCCGBank data file')
    parser.add_argument('--output',
                        help="Choose 'uni' or 'pair' or 'reveal. The former outputs the all of the combinators in the input data, and the latter outputs the combinators of a top-node and right-child-node.",
                        choices=['uni', 'pair', 'reveal'],
                        default='uni')
    args = parser.parse_args()

    if args.output == 'pair':
        CombinatorPairFinder.create_combinatorPairList(args)
    elif args.output == 'reveal':
        reveal_finder = RevealFinder(args.PATH)

        seen = []
        pathlist = reveal_finder.path_list
        for path in tqdm(pathlist):
            trees = [tree for _, _, tree in read_parsedtree(path)]
            for tree in tqdm(trees):
                reveal_finder._traverse(tree)
            for i in tqdm(reveal_finder.revealList):
                if i not in seen:
                    seen.append(i)

        stack = []
        # outputのpathを指定
        with open('/Users/kako/B4study-tools/BCCWJ-EyeTrack/data/CombinatorPair/reveal.txt', 'w') as f:
            for i in tqdm(sorted(seen)):
                print(f'op_symbol: {i[0]}, {i[1]}, {i[2]}', file=f)
                #
                #                sym: i[0], cat: i[3]
                #                   /            \
                #                  /              \
                #                 /                \
                #           cat: i[4]        sym: i[1], cat: i[5]
                #                              /           \
                #                             /             \
                #                            /               \
                #                 sym: i[2], cat: i[6]      cat: i[7]
                #                   /           \
                #                  /             \
                #                 /               \
                #            cat: i[8]          cat: i[9]
                #
                # {i[0] i[3] {i[4] 1/1/_/_} {i[1] i[5] {i[2] i[6] {i[8] 2/2/_/_} {i[9] 3/3/_/_}} {i[7] 4/4/_/_}}}
                stack.append('{' + i[0] + ' ' + i[3] + ' {' + i[4] + ' 1/1/_/_} {' + i[1] + ' ' +  i[5] + ' {' + i[2] + ' ' + i[6] + ' {' + i[8] + ' 2/2/_/_} {' + i[9] + ' 3/3/_/_}} {' + i[7] + ' 4/4/_/_}}}')
            f.write('\n')
            for i,j in tqdm(enumerate(read_parsedstring(stack))):
                f.write(str(i))
                f.write('\n')
                f.write(deriv_of(j))
                f.write('\n')

    else:
        CombinatorListCreator.create_combinatorlist(args)
