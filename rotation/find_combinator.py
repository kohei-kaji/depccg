import logging
import argparse
from pathlib import Path
from typing import List
from collections import defaultdict
from tqdm import tqdm

from depccg.tools.ja.reader import read_ccgbank
from depccg.printer.deriv import deriv_of
from depccg.tree import Tree

from parsed_reader import read_parsedtree, read_parsedstring
from tree_rotation import unification
# from tools import tokens

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class CombinatorListCreator(object):
    def __init__(self, path_list: List[str]):
        self.path_list = path_list
        self.combinator_dict = defaultdict(int)

    def _traverse(self, tree: Tree):
        if tree.is_leaf == False:
            children = tree.children
            if len(children) == 1:
                self._traverse(children[0])
                self.combinator_dict[tree.op_symbol] += 1
            else:
                self._traverse(children[0])
                self._traverse(children[1])
                self.combinator_dict[tree.op_symbol] += 1


class RightBranchFinder(object):
    def __init__(self, path_list: List[str]):
        self.path_list = path_list
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
                        help="Choose 'uni' or 'right' or 'reveal. If 'right' is choosen, the combinators of right-branching tree are outputted. If 'reveal' is choosen, the combinators of the tree in which a reveal operation counld be impremented are outputted. Else, all of the combinators are outputted",
                        choices=['uni', 'right', 'reveal'],
                        default='uni')
    args = parser.parse_args()

    if args.output == 'right':
        rightbranch_finder = RightBranchFinder(args.PATH)
        seen = []
        pathlist = rightbranch_finder.path_list
        for path in tqdm(pathlist):
            trees = [tree for _, _, tree in read_parsedtree(path)]
            for tree in tqdm(trees):
                rightbranch_finder._traverse(tree)
            for i in tqdm(rightbranch_finder.combinatorPairList):
                if i not in seen:
                    seen.append(i)

        stack = []
        OUTPUT_PATH = Path(args.PATH[0]).parent / 'rightbranch.txt'
        with open(OUTPUT_PATH, 'w') as f:
            logger.info(f'writing to {f.name}')
            for i in tqdm(sorted(seen)):
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
        OUTPUT_PATH = Path(args.PATH[0]).parent / 'reveal.txt'
        with open(OUTPUT_PATH, 'w') as f:
            logger.info(f'writing to {f.name}')
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
            for i in tqdm(read_parsedstring(stack)):
                if (unification(i.op_symbol,i.left_child.cat, i.right_child.cat) != None
                    and unification(i.right_child.op_symbol,i.right_child.left_child.cat, i.right_child.left_child.cat) != None
                    and unification(i.right_child.left_child.op_symbol,i.right_child.left_child.left_child.cat, i.right_child.left_child.right_child.cat) != None):
                    f.write(deriv_of(i))
                    f.write('\n')

    else:
        combinatorlist_creator = CombinatorListCreator(args.PATH)

        pathlist = combinatorlist_creator.path_list
        for path in tqdm(pathlist):
            trees = [tree for _, _, tree in read_ccgbank(path)]  # If input format is not Japanese CCGBank, change this function to 'read_parsedtree()'.
            for tree in tqdm(trees):
                combinatorlist_creator._traverse(tree)

        OUTPUT_PATH = Path(args.PATH[0]).parent / 'combinators.txt'
        with open(OUTPUT_PATH, 'w') as f:
            logger.info(f'writing to {f.name}')
            for key, value in tqdm(combinatorlist_creator.combinator_dict.items()):
                print(f'{key} # {str(value)}', file=f)
