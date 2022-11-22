import logging
import argparse
from pathlib import Path
from typing import List
from tqdm import tqdm

import numpy as np
import pandas as pd
from depccg.tree import Tree, Token
from parsed_reader import read_parsedtree
from rotation.typeraise import typeraise
from tools import can_combine, LeftSpine

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

# If the terminal node of ADN of left edge can be combine with the left sub-tree which is already created,
# CombinatorCount 1 is added to the left edge terminal node, and RotationCount 1 to the right edge terminal node.
#  Hanako-ga    Taro-o       nagutta     otoko-o
#  ---------  -----------   ---------   ---------
#     NP^         NP^       (S\NP)\NP      NP
#  --------------------->B
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

class RevealCombinatorCount(object):
    def __init__(self):
        self.combinator_list = []
        self.category_list = []
        self.adnominal_list = []
        # self.adnominal_tokens  = []
        # self.adnominal_count = 0
    # def traverse(self, node: Tree) -> None:
    #     if node.is_leaf == False:
    #         if node.is_unary:
    #             self.traverse(node.child)
    #             self.combinator_list.append(node.op_symbol)
    #         else:    #             self.traverse(node.left_child)
    #             self.traverse(node.right_child)
    #             self.combinator_list.append(node.op_symbol)
    #     else:
    #         self.combinator_list.append(node.op_symbol)

    def adnominal_traverse(self, node: Tree) -> None:
        self.tokens = node.tokens
        if node.is_leaf == False:
            if node.is_unary:
                if node.op_symbol.startswith('ADN'):  # Adnominal form (連体修飾形); ADNint, ADNext
                    self.adnominal_list.append(LeftSpine.output(node))
                    if can_combine(self.category_list[-1], self.adnominal_list[-1][-1]):
                        self.combinator_list.append('ROTATE')
                    else:
                        print([self.category_list[-1], self.adnominal_list[-1][-1]])
                    # self.adnominal_tokens.append(node.tokens)
                    # self.adnominal_count += 1

                self.adnominal_traverse(node.child)
                self.combinator_list.append(node.op_symbol)
                self.category_list.append(node.cat)
            else:
                self.adnominal_traverse(node.left_child)
                self.adnominal_traverse(node.right_child)
                self.combinator_list.append(node.op_symbol)
                self.category_list.append(node.cat)
        else:
            self.combinator_list.append(node.op_symbol)
            self.category_list.append(node.cat)


    @staticmethod
    def make_csv(trees: List[Tree], OUTPUT_PATH: str) -> None:
        self = RevealCombinatorCount()
        logger.info('traverse trees')
        for tree in tqdm(trees):
            self.adnominal_traverse(tree)

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

        reveal_count = []  # ADNのmost left-spineがその前のcategoryとcombineできるとき、left-spineに1, right-spineに2加えている (rotateとunary)
        logger.info('count reveal steps')
        rotate_occur = 0
        for i in tqdm(output_list):
            if 'ROTATE' in i:
                rotate_occur += 1
            count = str(i.count('ROTATE')
                        + i.count('>')
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
                        + i.count('SSEQ'))
            if rotate_occur == 1 and 'ANDint' in i:
                rotate_occur -= 1
                count += 1
            reveal_count.append(count)
        reveal_count = np.array(reveal_count)
        df = pd.DataFrame(np.stack([reveal_count],1), columns=['reveal count'])
        logger.info(f'writing to {OUTPUT_PATH}')
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
    OUTPUT_PATH = parent + '/' + file + '_combinators.csv'
    trees = [tree for _, _, tree in read_parsedtree(args.FILE)]
    CombinatorCount.make_csv(trees, OUTPUT_PATH)
