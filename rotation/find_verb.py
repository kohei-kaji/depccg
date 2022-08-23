"""
This finds VPs which are directlly combined with NP in Japanese CCGBank
so as to check out what combinations are there.

depccg/tools/ja/data.py is referred.
"""

import re
import logging
import argparse
from pathlib import Path
from typing import Dict
from collections import defaultdict

from depccg.tools.ja.reader import read_ccgbank
from depccg.tree import Tree

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class VerbListCreator(object):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.verb_list = defaultdict(int)
    
    def _traverse(self, tree: Tree):
        if tree.is_leaf == False:
            children = tree.children
            if len(children) == 1:
                self._traverse(children[0])
            else:
                self._traverse(children[0])
                self._traverse(children[1])
                if children[0].cat.is_atomic and children[0].cat.base == 'NP' and children[1].cat.is_functor: # if left is NP and right is a functor
                    s = str(children[1].cat)
                    if re.match(r'(\(*)S', s) is not None and s.count('S') == 1:  # if right starts with 'S' and right has only one 'S', that is, right is a VP
                        combination = str(children[0].cat), str(children[1].cat)
                        self.verb_list[combination] += 1
    
    @staticmethod
    def create_verblist(path: str) -> Dict[str, int]:
        self = VerbListCreator(path)

        trees = [tree for _, _, tree in read_ccgbank(self.filepath)]
        for tree in trees:
            self._traverse(tree)
            
        verb_list = {f'{c1} {c2}': v for (c1, c2), v in self.verb_list.items()}
        return verb_list

    @staticmethod
    def _write(dct, filename):
        with open(filename, 'w') as f:
            logger.info(f'writing to {f.name}')
            for key, value in dct.items():
                print(f'{key} # {str(value)}', file=f)

    @staticmethod
    def _create_verblist(args):
        self = VerbListCreator(args.PATH)

        trees = [tree for _, _, tree in read_ccgbank(self.filepath)]
        for tree in trees:
            self._traverse(tree)
            
        verb_list = {f'{c1} {c2}': v for (c1, c2), v in self.verb_list.items()}
        parent = Path(args.PATH).parent
        textname = str(Path(args.PATH).stem) + 'verb_list'
        self._write(verb_list, parent / textname)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH',
                        type=Path,
                        help='path to JapaneseCCGBank data file')
    
    args = parser.parse_args()

    VerbListCreator._create_verblist(args)
