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
    def make_csv(trees: List[Tree], output_path: str) -> None:
        self = CombinatorCount()
        logger.info('traversing trees')
        for tree in tqdm(trees):
            self.traverse(tree)

        stack = ['<lex>']
        output_list = []
        logger.info('corresponding combinators to each terminal')
        for i in tqdm(self.combinator_list):
            if i == '<lex>':
                output_list.append(stack)
                stack = ['<lex>']
            else:
                stack.append(i)
        output_list.append(stack)
        output_list = output_list[1:]

        binary_count = []
        typeraise_count = []
        # logger.info('remove <lex>')
        logger.info('counting binary combinators and >T')
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
                                + i.count('>B2')))
            typeraise_count.append(str(i.count('>T')))
            # i.remove('<lex>')
        # output_list = np.array(output_list)
        typeraise_count = np.array(typeraise_count)
        binary_count = np.array(binary_count)
        df = pd.DataFrame(np.stack([binary_count,typeraise_count],1), columns=['binary combinators', 'type-raising'])
        logger.info(f'writing to {output_path}')
        df.to_csv(output_path, index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('FILE',
                        type=str,
                        help='path to the input text file of parsed tree')

    args = parser.parse_args()
    parent = str(Path(args.FILE).parent)
    file = str(Path(args.FILE).stem)
    output_path = parent + '/' + file + '_combinators.csv'
    trees = [tree for _, _, tree in read_parsedtree(args.FILE)]
    CombinatorCount.make_csv(trees, output_path)
