from typing import Iterator, List, Tuple
from depccg.cat import Category
from depccg.tree import Tree
from depccg.types import Token
from depccg.tools.reader import ReaderResult
combinators = {
    'SSEQ', '>', '<', '>B', '<B1', '<B2', '<B3',
    '<B4', '>Bx1', '>Bx2', '>Bx3',
    'ADNext', 'ADNint', 'ADV0', 'ADV1', 'ADV2', '>T'
}
def read_parsedtree(line: str) -> Iterator[ReaderResult]:
    i = 1
    line = line.strip()
    tree, tokens = ParsedJaCCGLineReader(line).parse()
    yield ReaderResult(str(i), tokens, tree)
class ParsedJaCCGLineReader(object):
    def __init__(self, line: str) -> None:
        self.line = line
        self.index = 0
        self.word_id = -1
        self.tokens = []
    def next(self, target: str) -> str:
        end = self.line.find(target, self.index)
        result = self.line[self.index:end]
        self.index = end + 1
        return result
    def check(self, text: str, offset: int = 0) -> None:
        if self.line[self.index + offset] != text:
            raise RuntimeError('AutoLineReader.check catches parse error')
    def peek(self) -> str:
        return self.line[self.index]
    def parse(self) -> Tuple[Tree, List[Token]]:
        result = self.next_node()
        return result, self.tokens
    @property
    def next_node(self):
        end = self.line.find(' ', self.index)
        if self.line[self.index + 1:end] in combinators:
            return self.parse_tree
        else:
            return self.parse_leaf
    def parse_leaf(self) -> Tree:
        self.word_id += 1
        self.check('{')
        cat = self.next(' ')[1:]
        cat = Category.parse(cat)
        surf, base, pos1, pos2 = self.next('}')[:-1].split('/')
        token = Token(surf=surf, base=base, pos1=pos1, pos2=pos2)
        self.tokens.append(token)
        return Tree.make_terminal(surf, cat)
    def parse_tree(self) -> Tree:
        self.check('{')
        op_string = self.next(' ')
        # cat = DEPENDENCY.sub('', self.next(' '))
        cat = self.next(' ')
        cat = Category.parse(cat)
        self.check('{')
        children = []
        while self.peek() != '}':
            children.append(self.next_node())
            if self.peek() == ' ':
                self.next(' ')
        self.next('}')
        if len(children) == 1:
            return Tree.make_unary(cat, children[0], op_string.replace("{", ""), op_string.replace("{", ""))
        else:
            assert len(
                children) == 2, f'failed to parse, invalid number of children: {self.line}'
            left, right = children
            return Tree.make_binary(cat, left, right, op_string.replace("{", ""), op_string.replace("{", ""))
########### ↑ read_parsedtree #################

########### ↓ TreeRotation #################
import re
from typing import Dict, Optional

from depccg.cat import Category, Functor, Atom
from depccg.tree import Tree
from depccg.unification import Unification
from depccg.printer.ja import ja_of

# all the original combinators in the Japanese CCGBank
#   >, >B, >Bx1, >Bx2, >Bx3,
#   <, <B1, <B2, <B3, <B4,
#   ADV0, ADV1, ADV2, 
#   ADNint, ADNext, SSEQ

class TreeRotation(object):
    def __init__(self):     
        self.cat_to_order: Dict[str, int] = {
            '>':0,
            '<':0,
            '>B':1,
            '<B1':1,
            '<B2':2,
            '<B3':3,
            '<B4':4,
            '>Bx1':1,
            '>Bx2':2,
            '>Bx3':3
            }
        self.order_to_forwardstring: Dict[int, str] = {
            0: 'fa',
            1: 'fc',
            2: 'fc2'
        }
        
        self.order_to_forwardsymbol: Dict[int, str] = {
            0: '>',
            1: '>B',
            2: '>B2'
        }
    def forward(self, cat_symbol: str) -> bool:
        return (cat_symbol.startswith('>')) and ('x' not in cat_symbol)
    def clear_features(self, cat: Category) -> Category:
        if cat.is_functor:
            return Functor(
                self.clear_features(cat.left),
                cat.slash,
                self.clear_features(cat.right)
            )
        else:
            return Atom(cat.base)
    def rotate(self, node: Tree) -> Tree:
        if node.is_leaf:
            return node
        elif node.is_unary:
            return Tree.make_unary(node.cat,
                                   self.rotate(node.child),
                                   node.op_string,
                                   node.op_symbol)
        else:  # if node is binary
            return self.sinkForwardLeftward(Tree.make_binary(node.cat,
                                                        self.rotate(node.left_child),
                                                        self.rotate(node.right_child),
                                                        node.op_string,
                                                        node.op_symbol))
    
    def sinkForwardLeftward(self, top: Tree) -> Tree:
        if (top.is_unary == False) and (self.forward(top.op_symbol)):
            a = top.left_child
            right = top.right_child
            def rebuild(x: int, r: Tree) -> Optional[Tree]:
                if r.is_unary == False:  # if node is binary,
                    y = self.cat_to_order[r.op_symbol]
                    b, c = r.children
                    if (self.forward(r.op_symbol)) and (x >= y):
                        new_order = x-y+1
                        newl = rebuild(new_order, b)
                        if isinstance(newl, Tree):
                            return Tree.make_binary(top.cat,
                                                    newl,
                                                    c,
                                                    r.op_string,
                                                    r.op_symbol)
                        elif (newl == None) and (new_order <= 2):
                            uni = Unification("a/b", "b/c")
                            if uni(self.clear_features(a.cat),
                                   b.cat):  # ignore the features of a.cat in this momemt
                                newl_cat = Functor(a.cat.left, "/", uni["c"])
                                newl_string = self.order_to_forwardstring[new_order]
                                newl_symbol = self.order_to_forwardsymbol[new_order]
                                return Tree.make_binary(top.cat,
                                                        Tree.make_binary(newl_cat,
                                                                        a,
                                                                        b,
                                                                        newl_string,
                                                                        newl_symbol),
                                                        c,
                                                        r.op_string,
                                                        r.op_symbol)
                            else:
                                return None
                        else:
                            return None

                    elif (top.op_symbol == '>')\
                            and (r.op_symbol == '<')\
                                and (a.cat.right.base == 'NP')\
                                        and (c.cat.right.is_atomic)\
                                            and (c.cat.right.base == 'NP')\
                                                and (re.match(r'(\(*)NP', str(b.cat)) is not None):
                        uni = Unification("a/b", "b")
                        if uni(self.clear_features(a.cat),
                                   b.cat):
                            newl_cat = a.cat.left
                            return Tree.make_binary(top.cat,
                                                    Tree.make_binary(newl_cat,
                                                                    a,
                                                                    b,
                                                                    'fa',
                                                                    '>'),
                                                    c,
                                                    'ba',
                                                    '<')
                        else:
                            return None
                    else:
                        return None
                else:
                    return None

            rebranch = rebuild(self.cat_to_order[top.op_string],
                               right)
            
            if isinstance(rebranch, Tree):
                return rebranch
            else:
                return top
        else:
            return top
    
    @staticmethod
    def return_rotated_tree(line):
        self = TreeRotation(line)

        trees = [tree for _, _, tree in read_parsedtree()]
        for tree in trees:
            tree = self.rotate2left(tree)
            print(ja_of(tree))

if __name__ == '__main__':
    # s = r"{< S[mod=nm,form=base,fin=t] {> S[mod=nm,form=base,fin=f] {< S[mod=X1,form=X2,fin=f]/S[mod=X1,form=X2,fin=f] {< S[mod=X1,form=X2,fin=f]/S[mod=X1,form=X2,fin=f] {> S[mod=nm,form=base,fin=f] {>T S[mod=X1,form=X2,fin=X3]/(S[mod=X1,form=X2,fin=X3]\NP[case=X1,mod=X2,fin=X3]) {< NP[case=ga,mod=nm,fin=f] {> NP[case=nc,mod=nm,fin=f] {ADNint NP[case=nc,mod=X1,fin=X2]/NP[case=nc,mod=X1,fin=X2] {>Bx1 S[mod=adn,form=base,fin=f]\NP[case=ga,mod=nm,fin=f] {ADV0 S[mod=X1,form=X2,fin=X3]/S[mod=X1,form=X2,fin=X3] {< S[mod=adv,form=cont,fin=f] {S[mod=nm,form=cont,fin=f] 呼び出し/呼び出し/_/_} {S[mod=adv,form=cont,fin=f]\S[mod=nm,form=cont,fin=f] て/て/_/_}}} {<B1 S[mod=adn,form=base,fin=f]\NP[case=ga,mod=nm,fin=f] {S[mod=nm,form=stem,fin=f]\NP[case=ga,mod=nm,fin=f] 注意/注意/_/_} {S[mod=adn,form=base,fin=f]\S[mod=nm,form=stem,fin=f] する/する/_/_}}}} {NP[case=nc,mod=nm,fin=f] 先生/先生/_/_}} {NP[case=ga,mod=nm,fin=f]\NP[case=nc,mod=nm,fin=f] も/も/_/_}}} {<B1 S[mod=nm,form=base,fin=f]\NP[case=ga,mod=nm,fin=f] {S[mod=nm,form=cont,fin=f]\NP[case=ga,mod=nm,fin=f] い/い/_/_} {S[mod=nm,form=base,fin=f]\S[mod=nm,form=cont,fin=f] た/た/_/_}}} {(S[mod=X1,form=X2,fin=f]/S[mod=X1,form=X2,fin=f])\S[mod=nm,form=base,fin=f] が/が/_/_}} {(S[mod=X1,form=X2,fin=f]/S[mod=X1,form=X2,fin=f])\(S[mod=X1,form=X2,fin=f]/S[mod=X1,form=X2,fin=f]) 、/、/_/_}} {> S[mod=nm,form=base,fin=f] {>T S[mod=X1,form=X2,fin=X3]/(S[mod=X1,form=X2,fin=X3]\NP[case=X1,mod=X2,fin=X3]) {< NP[case=ga,mod=nm,fin=f] {> NP[case=nc,mod=nm,fin=f] {ADNint NP[case=nc,mod=X1,fin=X2]/NP[case=nc,mod=X1,fin=X2] {> S[mod=adn,form=base,fin=f] {< S[mod=X1,form=X2,fin=f]/S[mod=X1,form=X2,fin=f] {> NP[case=nc,mod=nm,fin=f] {< NP[case=X1,mod=X2,fin=f]/NP[case=X1,mod=X2,fin=f] {NP[case=X1,mod=X2,fin=f]/NP[case=X1,mod=X2,fin=f] 二/二/_/_} {(NP[case=X1,mod=X2,fin=f]/NP[case=X1,mod=X2,fin=f])\(NP[case=X1,mod=X2,fin=f]/NP[case=X1,mod=X2,fin=f]) 、/、/_/_}} {< NP[case=nc,mod=nm,fin=f] {< NP[case=nc,mod=nm,fin=f] {NP[case=nc,mod=nm,fin=f] 三/三/_/_} {NP[case=nc,mod=nm,fin=f]\NP[case=nc,mod=nm,fin=f] 年/年/_/_}} {NP[case=nc,mod=nm,fin=f]\NP[case=nc,mod=nm,fin=f] 時/時/_/_}}} {(S[mod=X1,form=X2,fin=f]/S[mod=X1,form=X2,fin=f])\NP[case=nc,mod=nm,fin=f] に/に/_/_}} {< S[mod=adn,form=base,fin=f] {> S[mod=nm,form=cont,fin=f] {>T S[mod=X1,form=X2,fin=X3]/(S[mod=X1,form=X2,fin=X3]\NP[case=X1,mod=X2,fin=X3]) {NP[case=nc,mod=nm,fin=f] 担任/担任/_/_}} {S[mod=nm,form=cont,fin=f]\NP[case=nc,mod=nm,fin=f] だっ/だっ/_/_}} {S[mod=adn,form=base,fin=f]\S[mod=nm,form=cont,fin=f] た/た/_/_}}}} {> NP[case=nc,mod=nm,fin=f] {>B NP[case=X1,mod=X2,fin=f]/NP[case=X1,mod=X2,fin=f] {NP[case=X1,mod=X2,fin=f]/NP[case=X1,mod=X2,fin=f] 池田/池田/_/_} {>B NP[case=X1,mod=X2,fin=f]/NP[case=X1,mod=X2,fin=f] {NP[case=X1,mod=X2,fin=f]/NP[case=X1,mod=X2,fin=f] 弘子/弘子/_/_} {NP[case=X1,mod=X2,fin=f]/NP[case=X1,mod=X2,fin=f] 先生/先生/_/_}}} {< NP[case=nc,mod=nm,fin=f] {> NP[case=nc,mod=nm,fin=f] {NP[case=X1,mod=X2,fin=f]/NP[case=X1,mod=X2,fin=f] （/（/_/_} {> NP[case=nc,mod=nm,fin=f] {NP[case=X1,mod=X2,fin=f]/NP[case=X1,mod=X2,fin=f] ７/７/_/_} {NP[case=nc,mod=nm,fin=f] ５/５/_/_}}} {NP[case=nc,mod=nm,fin=f]\NP[case=nc,mod=nm,fin=f] ）/）/_/_}}}} {NP[case=ga,mod=nm,fin=f]\NP[case=nc,mod=nm,fin=f] は/は/_/_}}} {<B1 S[mod=nm,form=base,fin=f]\NP[case=ga,mod=nm,fin=f] {S[mod=nm,form=cont,fin=f]\NP[case=ga,mod=nm,fin=f] 違っ/違っ/_/_} {S[mod=nm,form=base,fin=f]\S[mod=nm,form=cont,fin=f] た/た/_/_}}}} {S[mod=nm,form=base,fin=t]\S[mod=nm,form=base,fin=f] 。/。/_/_}}"
    
    s = r"{> NP[case=o,mod=nm,fin=f] {NP[case=o,mod=nm,fin=f]/NP[case=ga,mod=nm,fin=f] 形容詞/形容詞/_/_} {< NP[case=ga,mod=nm,fin=f] {NP[case=nc,mod=nm,fin=f] 名詞/名詞/_/_} {NP[case=ga,mod=nm,fin=f]\NP[case=nc,mod=nm,fin=f] 後置詞/後置詞/_/_}}}"
    a = r"{< NP[case=o,mod=nm,fin=f] {> NP[case=o,mod=nm,fin=f] {NP[case=o,mod=nm,fin=f]/NP[case=ga,mod=nm,fin=f] 形容詞/形容詞/_/_} {NP[case=nc,mod=nm,fin=f] 名詞/名詞/_/_}} {NP[case=ga,mod=nm,fin=f]\NP[case=nc,mod=nm,fin=f] 後置詞/後置詞/_/_}}"
    rotation = TreeRotation()
    trees = [tree for _, _, tree in read_parsedtree(s)]
    tree = rotation.rotate(trees[0])
    print(ja_of(tree) == a)
