import argparse
import numpy as np
from typing import List

from depccg.utils import denormalize
from depccg.printer.html import _MATHML_MAIN, _mathml_subtree
from depccg.printer.ja import ja_of
from pathlib import Path
from depccg.tree import Tree

from clear_features import clear_features
from ccgbank_reader import read_ccgbank
from parsed_reader import read_parsedtree

# rewrite auto_of (depccg/printer/auto.py)
def featureless_auto_of(tree: Tree) -> str:
    """tree string in auto format which discards ternary features

    Args:
        tree (Tree): tree object

    Returns:
        str: tree string in the auto format
    """
    def rec(node):
        if node.is_leaf:
            cat = node.cat
            cat = clear_features(cat)
            word = denormalize(node.word)
            pos = node.token.get('pos', 'POS')
            return f'(<L {cat} {pos} {pos} {word} {cat}>)'
        else:
            cat = node.cat
            cat = clear_features(cat)
            children = ' '.join(rec(child) for child in node.children)
            num_children = len(node.children)
            head_is_left = 0 if node.head_is_left else 1
            return f'(<T {cat} {head_is_left} {num_children}> {children} )'

    return rec(tree)

def trees_to_auto(output_path: str, trees: List[Tree]):
    """rewrite Japanese CCGBank with English CCGBank format.

    Args:
        filepath (str): file name string

    Results:
        text file which contains Japanese CCGBank of the English CCGBank format
    """
    with open(output_path, 'w') as f:
        for tree in trees:
            f.write(featureless_auto_of(tree))
            f.write('\n')

def ja_to_html(output_path: str, trees: List[Tree]):
    """rewrite Japanese CCGBank with the html format.

    Args:
        filepath (str): file name string

    Results:
        str: html format (refer to ./depccg/printer/html.py)
    """
    with open(output_path, 'w') as f:
        for tree in trees:
            result = ''
            words = tree.word
            result += f'<p>{words}</p>'
            tree_str = tree if isinstance(tree, str) else _mathml_subtree(tree)
            result += f'<math xmlns="http://www.w3.org/1998/Math/MathML">{tree_str}</math>'
            f.write(_MATHML_MAIN.format(result))
            f.write('\n')

def trees_to_ja(output_path: str, trees: List[Tree]):
    with open(output_path, 'w') as f:
        for tree in trees:
            f.write(ja_of(tree))
            f.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('FILE', type=str, help='path to the input text file')
    parser.add_argument('--input',
                        choices=['CCGBank', 'parsed'],
                        default='CCGBank')
    parser.add_argument('--output',
                        choices=['html', 'auto'],
                        default='html')

    args = parser.parse_args()
    parent = str(Path(args.FILE).parent)
    file = str(Path(args.FILE).stem)

    if args.input == 'parsed':
        trees = [tree for _, _, tree in read_parsedtree(args.FILE)]
        if args.output == 'auto':
            output_name = parent + '/' + file + '_auto'
            trees_to_auto(output_name, trees)
        else:
            for id, trees in enumerate(np.array_split(trees, 4)):
                output_name = parent + '/' + file + str(id) + '.html'
                ja_to_html(output_name, trees)

    else:
        trees = [tree for _, _, tree in read_ccgbank(args.FILE)]
        if args.output == 'auto':
            output_name = parent + '/' + file + '_auto'
            trees_to_auto(output_name, trees)
        else:
            output_name = parent + '/' + file + '.html'
            ja_to_html(output_name, trees)
