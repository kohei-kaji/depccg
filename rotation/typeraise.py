"""
Japanese CCGBankにtype-raising ruleを導入した上で、NPに対し、type-raisingを適用する。

(方針)
1. Japanese CCGBankをTreeオブジェクトとして読み込む。
2. top-node (S) から順に見ていき、NP S\NP -> S のように動詞句とcombineされているとき、NPにtype-raisingを適用する。
    - このとき、NPの上にS/(S\NP) nodeを作り、combinatorを変更する。
        - NPの下にmake_unary (S/(S\NP)) した上で、NPとS\NPのcombinatorを変更し、その上でNPとS/(S\NP)の位置を入れ替えればよい。
    - これをひとつの関数で実装し、再起的にleaf nodeまで探索する。(depccg/printerの再帰関数を参考)
3. Treeオブジェクトを書き換えたら、文字列として出力する。
    - この際、html出力ができるようにすると、簡易的なチェックが可能。

(要検討)
- type-raisingが適用される条件はrule-baseで設定する。
    - どのような条件？
- 
"""
import re
# from collections import defaultdict

from typing import Dict, List

from depccg.cat import Category, Atom, Functor
from depccg.tree import Tree
from depccg.types import CombinatorResult
from depccg.unification import Unification
from depccg.grammar.en import _is_type_raised


class ApplyTypeRaise(object):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tr_rules: Dict[str, str] = {}
    
    def readdict(self, dictpath: str):
        with open(dictpath, 'r') as f:
            for line in f:
                self.tr_rules[line[0]] = line[1]
        return self.tr_rules
    
    # X -> T/(T\X)
    def apply_tr_rules(self, x: Atom, y:Functor) -> Functor:
        results = [result for result in self.tr_rules[x.base] 
        if Category.parse(result).right == y
        and x == Category.parse(result).right.right]
        return results[0]
        # uni = Unification("a/b", "b")
        # tr: Functor = Category.parse(self.tr_rules[str(x)])
        
        # if uni(tr, y):
        #     return tr
        # else:
        #     raise Exception
        
        
    def _traverse(self, tree: Tree):
        if tree.is_leaf == False:
            children = tree.children
            if len(children) == 1:
                self._traverse(children[0])
            else:
                left = children[0]
                right = children[1]
                self._traverse(left)
                self._traverse(right)
                if left.cat.is_atomic and left.cat.base == 'NP' and right.cat.is_functor: # if left is NP and right is a functor
                    s = str(right.cat)
                    if re.match(r'(\(*)S', s) is not None:  # if right starts with S, that is, right is VP
                        typeraise = self.apply_tr_rules(left, right)
                        origin_cat = left.cat
                        origin_children = left.children
                        left.children = [Tree(origin_cat, origin_children, 'tr', '<tr>')]
                        left.cat = typeraise
                        tree.op_string = 'fa'
                        tree.op_symbol = '>'
                        


#################################################
# 新たに導入するtype raising rule群
# 要検討
# 素性指定をするべきか否か。
# Atom.baseは、feature含めたstrでは？ -> 辞書はNPではなく、NP[case=ga, ...]で用意しなければ？
# forward type-raisingのみのdictにする。

# {key <- VP, value <- type-raised NP}
tr_rules: Dict[str, str] = {
    "S[mod=nm,form=da,fin=f]\NP[case=ga,mod=nm,fin=f]": "S[mod=X1,form=X2,fin=X3]/(S[mod=X1,form=X2,fin=X3]\NP[mod=X1,form=X2,fin=X3])",
    }
