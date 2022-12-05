import re
import logging
import argparse
from pathlib import Path
from typing import List
from tqdm import tqdm

import numpy as np
import pandas as pd
from depccg.cat import Category
from depccg.tree import Tree, Token
from parsed_reader import read_parsedtree

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class NodeCount(object):
    def __init__(self):
        self.count = 1
        self.counts = []

    def traverse(self, node: Tree) -> None:
        if node.is_leaf == False:
            children = node.children
            if len(children) == 1:
                self.traverse(children[0])
                self.count += 1
            else:
                self.traverse(children[0])
                self.traverse(children[1])
                self.count += 1
        else:
            self.counts.append(self.count)
            self.count += 1

def nodecount(filepath: str, trees: List[Tree]):
    """Count the number of nodes by bottom-up traversal

    Args:
        filepath (str): input text file parsed by depccg (Ja format)

    Results:
        output csv file
    """
    tokens: List[Token] = []
    counts: List[int] = []
    for tree in trees:
        nd = NodeCount()
        nd.traverse(tree)
        nd.counts.append(nd.count)
        tokens += [token['word'] for token in tree.tokens]
        counts += [j-i for i,j in zip(nd.counts, nd.counts[1:])]

    arr_tokens = np.array(tokens, dtype=object)
    arr_counts = np.array(counts, dtype=object)
    results = np.stack([arr_tokens, arr_counts])
    np.savetxt(filepath, results.T, fmt="%s", delimiter=',', newline='\n')

# top-down traversal
# class TopDonwCombinatorCount(object):
#     def __init__(self):
#         self.combinator_list = []
#     def traverse(self, node: Tree) -> None:
#         if node.is_leaf == False:
#             self.combinator_list.append(node.op_symbol)
#             children = node.children
#             if len(children) == 1:
#                 self.traverse(children[0])
#             else:
#                 self.traverse(children[0])
#                 self.traverse(children[1])
#         else:
#             self.combinator_list.append(node.op_symbol)


# bottom-up traversal
class CombinatorCount(object):
    def __init__(self):
        self.combinator_list = []
    def traverse(self, node: Tree) -> None:
        if node.is_leaf == False:
            children = node.children
            if len(children) == 1:
                self.traverse(children[0])
                self.combinator_list.append(node.op_symbol)
            else:
                self.traverse(children[0])
                self.traverse(children[1])
                self.combinator_list.append(node.op_symbol)
        else:
            self.combinator_list.append(node.op_symbol)

    @staticmethod
    def make_csv(trees: List[Tree], OUTPUT_PATH: str) -> None:
        self = CombinatorCount()
        logger.info('traverse trees')
        for tree in tqdm(trees):
            self.traverse(tree)

        stack = ['<lex>']
        output_list = []
        logger.info('make combinators correspond to each terminal')
        for i in tqdm(self.combinator_list):
            if i == '<lex>':
                output_list.append(stack)
                stack = ['<lex>']
            else:
                stack.append(i)
        output_list.append(stack)
        output_list = output_list[1:]

        binary_count = []
        # logger.info('remove <lex>')
        logger.info('count binary combinators')
        for i in tqdm(output_list):
            binary_count.append(str(i.count('>')
                                + i.count('<')
                                + i.count('>B')
                                + i.count('<B1')
                                + i.count('<B2')
                                + i.count('<B3')
                                + i.count('<B4')
                                + i.count('>Bx1')
                                + i.count('>Bx2')
                                + i.count('>Bx3')
                                + i.count('>B2')
                                + i.count('SSEQ')))
            # i.remove('<lex>')
        # output_list = np.array(output_list)
        binary_count = np.array(binary_count)
        df = pd.DataFrame(np.stack([binary_count],1), columns=['binary combinators'])
        logger.info(f'writing to {OUTPUT_PATH}')
        df.to_csv(OUTPUT_PATH, index=False)

# In contrast to Stanojevic et al. (2021; 2022), the operation, Rotate-to-right, will happen only when it is necessary.
# That is, when the unary rules, ADNint or ADNext, is applied, as follows;
#      0          1            1       2 + rotate(=1)
#  Hanako-ga    Taro-o      nagutta     otoko-o
#  ---------  ----------   ---------   ---------
#     NP^         NP^      (S\NP)\NP       NP
#  -------------------->B
#      S/((S\NP)\NP)
#  ---------------------------------->
#                  S
#  ---------------------------[rotate]
#  ---------  -----------------------
#   S/(S\NP)           S\NP
#             -------------------[ADN]
#                     NP/NP
#             ---------------------------------->
#                            NP^
#  --------------------------------------------->B
#                 S/((S\NP)\NP)
#
# I focus on the fact that top-down traversal can detect the left-spine of a constituent,
# and bottom-up traversal can detect the right-spine of a constituent.
#
# Now, I call the constituent including 'ADNint' an 'ADN constituent'.
# The terminal node of the left-spine of an ADN constituent is added 1 to, when
#   (1) the terminal node is not the beggining of a sentence, and
#   (2) the terminal node can combine with the category already constructed in bottom-up traversal
# On the other hand, the terminal node located in the right of the right-spine of an ADN constituent is added [rotation count] to, when
#   (1) there is at least one binary composition under ADN, and
#   (2) the ADN constituent is not the end of a sentence.

def most_left_cat(cat: Category) -> str:
    s = str(cat)
    if re.match(r'\(*S', s) is not None:
        return 'S'
    else:
        return 'NP'

def can_combine(l: str, r: str) -> bool:
    l = Category.parse(l)
    r = Category.parse(r)
    if l.is_atomic:
        return False
    else:
        match l.slash:
            case '/':
                if l.right.is_atomic:
                    return str(l.right) == most_left_cat(r)
                else:
                    if r.is_atomic:
                        return l.right == r
                    else:
                        return l.right == r.left
            case '\\':
                if r.is_atomic:
                    return False
                else:
                    if r.slash == '/':
                        return False
                    else:
                        return l.left == r.right

class RevealCombinatorCount(object):
    def __init__(self):
        self.bu_combinator_list = []
        self.bu_category_list = []
        self.td_combinator_list = []

    def bottomup_traverse(self, node: Tree) -> None:
        if node.is_leaf == False:
            children = node.children
            if len(children) == 1:
                self.bottomup_traverse(children[0])
                self.bu_combinator_list.append(node.op_symbol)
                self.bu_category_list.append(str(node.cat))
            else:
                self.bottomup_traverse(children[0])
                self.bottomup_traverse(children[1])
                self.bu_combinator_list.append(node.op_symbol)
                self.bu_category_list.append(str(node.cat))
        else:
            self.bu_combinator_list.append(node.op_symbol)
            self.bu_category_list.append('terminal')
            self.bu_category_list.append(str(node.cat))

    def topdown_traverse(self, node: Tree) -> None:
        if node.is_leaf == False:
            self.td_combinator_list.append(node.op_symbol)
            children = node.children
            if len(children) == 1:
                self.topdown_traverse(children[0])
            else:
                self.topdown_traverse(children[0])
                self.topdown_traverse(children[1])
        else:
            self.td_combinator_list.append(node.op_symbol)

    @staticmethod
    def make_csv(trees: List[Tree], OUTPUT_PATH: str) -> None:
        reveal_counts = []
        for tree in tqdm(trees):
            self = RevealCombinatorCount()
            self.bottomup_traverse(tree)
            self.topdown_traverse(tree)

            stack = []
            bu_combinator_list = []
            for i in self.bu_combinator_list:
                if i == "<lex>":
                    bu_combinator_list.append(stack)
                    stack = []
                else:
                    stack.append(i)
            bu_combinator_list.append(stack)
            bu_combinator_list = bu_combinator_list[1:]

            stack = []
            bu_category_list = []
            for i in self.bu_category_list:
                if i == "terminal":
                    bu_category_list.append(stack)
                    stack = []
                else:
                    stack.append(i)
            bu_category_list.append(stack)
            bu_category_list = bu_category_list[1:]

            stack = []
            td_combinator_list = []
            for i in self.td_combinator_list:
                if i == "<lex>":
                    td_combinator_list.append(stack)
                    stack = []
                else:
                    stack.append(i)
            td_combinator_list.append(stack)
            td_combinator_list.pop()

            reveal_count = [0]*len(bu_combinator_list)
            if 'ADNint' in td_combinator_list[0]:
                adn_count = td_combinator_list[0].count('ADNint')
                counter = 0
                while counter != adn_count:
                    for combinators in bu_combinator_list:
                        if 'ADNint' in combinators:
                            c_count = combinators.count('ADNint')
                            if c_count <= adn_count-counter:
                                for i in range(c_count):
                                    combinators.remove('ADNint')
                                counter += c_count
                            else:
                                while adn_count-counter != 0:
                                    combinators.remove('ADNint')
                                    counter += 1

            for pointer, bu_combinators in enumerate(bu_combinator_list[2:], 2):
                if len(bu_combinators) == 0:
                    if can_combine(bu_category_list[pointer-1][-1], bu_category_list[pointer][-1]):
                        reveal_count[pointer] += 1
                elif len(bu_combinators) == 1:
                    if bu_combinators.count('>T') == 1:
                        if can_combine(bu_category_list[pointer-1][-1], bu_category_list[pointer][-1]):
                            reveal_count[pointer] += 1
                else:
                    reveal_count[pointer] += 1

                # if 'ADNint' in bu_combinators:
                #     if ('>' in bu_combinators
                #         or '<' in bu_combinators
                #         or '>B' in bu_combinators
                #         or '<B1' in bu_combinators
                #         or '<B2' in bu_combinators
                #         or '<B3' in bu_combinators
                #         or '<B4' in bu_combinators
                #         or '>Bx1' in bu_combinators
                #         or '>Bx2' in bu_combinators
                #         or '>Bx3' in bu_combinators
                #         or '>B2' in bu_combinators
                #         or 'SSEQ' in bu_combinators):
                #         reveal_count[pointer+1] += 1
            # for pointer, td_combinators in enumerate(td_combinator_list):
            #     if 'ADNint' in td_combinators:
            #         if can_combine(bu_category_list[pointer-1][-1], bu_category_list[pointer][-1]):
            #             reveal_count[pointer] += 1

            reveal_counts.append(reveal_count)

        output_list = []
        for count in reveal_counts:
            output_list += count
        output_list = np.array(output_list, dtype=np.int64)
        df = pd.DataFrame(np.stack([output_list],1), columns=["reveal"])
        df.to_csv(OUTPUT_PATH, index=False)


# Open Node Count of bottom-up traversal, following Nelson et al. (2017)?

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('FILE',
                        type=Path,
                        help='path to the input text file of parsed tree')

    args = parser.parse_args()
    parent = str(Path(args.FILE).parent)
    file = str(Path(args.FILE).stem)
    # OUTPUT_PATH = parent + '/' + file + '_combinators.csv'
    OUTPUT_PATH = parent + '/' + file + '_reveal.csv'
    trees = [tree for _, _, tree in read_parsedtree(args.FILE)]
    # CombinatorCount.make_csv(trees, OUTPUT_PATH)
    RevealCombinatorCount.make_csv(trees, OUTPUT_PATH)
