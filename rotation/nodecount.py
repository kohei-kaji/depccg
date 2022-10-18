import argparse
from pathlib import Path
from typing import List
from collections import defaultdict

import numpy as np
from depccg.tree import Tree, Token
from parsed_reader import read_parsedtree

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


class CombinatorCount(object):
    def __init__(self):
        self.combinator_dict = defaultdict(int)
        self.stack = []
    def traverse(self, node: Tree) -> None:
        if node.is_leaf == False:
            children = node.children
            if len(children) == 1:
                self.traverse(children[0])
                self.combinator_dict[node.op_symbol] += 1
            else:
                self.traverse(children[0])
                self.traverse(children[1])
                self.combinator_dict[node.op_symbol] += 1
        else:
            self.stack.append(self.combinator_dict)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('FILE',
                        type=str,
                        help='path to the input text file of parsed tree')

    args = parser.parse_args()
    parent = str(Path(args.FILE).parent)
    file = str(Path(args.FILE).stem)
    output_path = parent + '/' + file + '_nodecount.csv'
    trees = [tree for _, _, tree in read_parsedtree(args.FILE)]
    nodecount(output_path, trees)
