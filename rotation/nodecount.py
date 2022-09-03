import argparse
from pathlib import Path
from typing import Tuple, List

from depccg.tree import Tree, Token
from reader import read_parsedtree

class NodeCount(object):
    def __init__(self):
        self.count = 1
        self.results = []

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
            self.results.append(self.count)
            self.count += 1
        ##########################################################
    	##### binary treeのみで挙動確認。type-raise含みについては未確認。
    	##########################################################

def nodecount(tree: Tree) -> Tuple[List[Token], List[int]]:
    nd = NodeCount()
    nd.traverse(tree)
    nd.results.append(nd.count)
    results = [j-i for i,j in zip(nd.results, nd.results[1:])]
    tokens = [token['word'] for token in tree.tokens]
    ##########################################################
    ##### Tokenに'word'しかないかは未確認。
    ##########################################################
    
    return tokens, results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('FILE',
                        type=str,
                        help='path to the input text file of parsed tree')
    
    args = parser.parse_args()
    parent = str(Path(args.FILE).parent)
    file = str(Path(args.FILE).stem)
    
    trees = [tree for _, _, tree in read_parsedtree(args.FILE)]
    output_path = parent + '/' + file + '_nodecount'
    
    for tree in trees:
    	tokens, results = nodecount(tree)
    ##########################################################
    ##### ファイルへの書き込み
    ##### tokens, resultsをcsvに縦に書き込めば後々楽か
    ##########################################################
    
    