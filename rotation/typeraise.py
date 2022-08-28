# (方針)
# 1. Japanese CCGBankをTreeオブジェクトとして読み込む。
# 2. top-node (S) から順に見ていき、NP S\NP -> S のように動詞句とcombineされているとき、NPにtype-raisingを適用する。
#     - このとき、NPの上にS/(S\NP) nodeを作り、combinatorを変更する。
#         - NPの下にmake_unary (S/(S\NP)) した上で、NPとS\NPのcombinatorを変更し、その上でNPとS/(S\NP)の位置を入れ替えればよい。
#     - これをひとつの関数で実装し、再起的にleaf nodeまで探索する。(depccg/printerの再帰関数を参考)
# 3. Treeオブジェクトを書き換えたら、文字列として出力する。
#     - この際、html出力ができるようにすると、簡易的なチェックが可能。

import re
import argparse
from typing import Dict, List
from pathlib import Path

from depccg.cat import Category, Atom, Functor
from depccg.tree import Tree
from depccg.unification import Unification
from depccg.printer.ja import ja_of

from reader import read_parsedtree


class ApplyTypeRaise(object):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tr_rules: Dict[str, str] = {}  # Dict[right-node, type-raised left-node]
    
    def readdict(self, dictpath: str = '/Users/kako/depccg/rotation/trdict.txt'):
        with open(dictpath, 'r') as f:
            for line in f:
                line = line.split()
                self.tr_rules[line[0]] = line[1]
        return self.tr_rules
    
    # X -> T/(T\X)
    def apply_tr_rules(self, x: Atom, y:Functor) -> Functor:
        # results = [result for result in self.tr_rules[x.base]
        # if Category.parse(result).right == y
        # and x == Category.parse(result).right.right]
        # return results[0]
        uni = Unification("a/b", "b")
        tr: Functor = Category.parse(self.tr_rules[str(y)])
        
        if uni(tr, y):
            return tr
        else:
            raise Exception
        
        
    def _traverse(self, tree: Tree) -> None:
        if tree.is_leaf == False:
            if len(tree.children) == 1:
                self._traverse(tree.children[0])
            else:
                left, right = tree.children
                self._traverse(left)
                self._traverse(right)
                if left.cat.is_atomic and left.cat.base == 'NP' and right.cat.is_functor: # if left is NP and right is a functor
                    s = str(right.cat)
                    if re.match(r'(\(*)S', s) is not None and s.count('S') == 1:  # if right starts with S, that is, right is VP
                        
                        np_cat = left.cat
                        np_children = left.children
                        np_op_string = left.op_string
                        np_op_symbol = left.op_symbol
                        
                        tr_cat = self.apply_tr_rules(left.cat, right.cat)
                        tr_children = [Tree(np_cat, np_children, np_op_string, np_op_symbol)]
                        
                        
                        s_cat = tree.cat
                        s_children = tree.children
                        s_op_string = tree.op_string
                        s_op_symbol = tree.op_symbol
                        
                        
                        tree.left_child.children = [Tree(left.cat, left.children, left.op_string, left.op_symbol)]
                        # tree.children = [Tree(tr_cat, [tree.left_child], 'tr', '>T'), right]
                        # tree = Tree(tree.cat, tree.children, 'fa', '>')
                        # tree.children = [Tree(tr_cat, tr_children, 'tr', '>T'), right]
                        # tree = Tree(tree.cat, tree.children, 'fa', '>')
                        # tree.op_string = 'fa'
                        # tree.op_symbol = '>'
                       
                        # tree = Tree(tree_cat, [tree_left, right], 'fa', '>')
                        # tree.children = [Tree(typeraise, origin_children, 'tr', '>T'), right]
                        # tree.left_child.children = origin_children
                        
                        # tree.left_child.children = np_children
                        # tree.children = [Tree(typeraise, origin_children, 'tr', '>T'), right]
                        # tree = Tree(tree_cat, [tree_left, right], 'fa', '>')
                                                         
                        
                        
                        
                        # tree.left_child.children: List[Tree] = [Tree(origin_cat, origin_children, origin_op_string, origin_op_symbol)]
                        # tree.children: List[Tree] = [Tree(typeraise, tree.left_child.children, 'tr', '>T')]
                        # # tree.op_string, tree.op_symbol = 'fa', '>'
                        # tree = Tree(tree_cat, tree.children, 'fa', '>')
    
    @staticmethod
    def typeraise(args):
        self = ApplyTypeRaise(args.PATH)
        self.readdict()
        
        parent = Path(self.filepath).parent
        textname = str(Path(self.filepath).stem) + '_typeraised'
        trees = [tree for _, _, tree in read_parsedtree(self.filepath)]
        with open(parent / textname, 'w') as f:
            for tree in trees:
                self._traverse(tree)
                f.write(ja_of(tree))
                f.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH',
                        type=Path,
                        help='path to the file of the Japanese CCG derivations parsed by depccg')
    
    args = parser.parse_args()
    ApplyTypeRaise.typeraise(args)
                        


#################################################
# 新たに導入するtype raising rule群
# 要検討
# 素性指定をするべきか否か。
# Atom.baseは、feature含めたstrでは？ -> 辞書はNPではなく、NP[case=ga, ...]で用意しなければ？
# forward type-raisingのみのdictにする。

# {key <- VP, value <- type-raised NP}
# tr_rules: Dict[str, str] = {
#     "S[mod=nm,form=da,fin=f]\NP[case=ga,mod=nm,fin=f]": "S[mod=X1,form=X2,fin=X3]/(S[mod=X1,form=X2,fin=X3]\NP[mod=X1,form=X2,fin=X3])",
#     }
