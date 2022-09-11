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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH',
                        type=Path,
                        help='path to JapaneseCCGBank data file')

    args = parser.parse_args()

    CombinatorListCreator.create_combinatorlist(args)
