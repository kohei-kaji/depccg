import re
from depccg.cat import Category


def is_vp(cat: Category) -> bool:
    """
    A functor category is VP when
        1. it includes just one 'S' category and
        2. it starts with 'S' category and
        3. it has no forward slash ('/').
    """
    s = str(cat)
    return (cat.is_functor
            and s.count('S') == 1
            and re.match(r'\(*S', s) is not None
            and re.search(r'/', s) is None)

def madeof(cat: Category):
    s = set()
    def rec(c):
        if c.is_functor:
            rec(c.left)
            rec(c.right)
        else:
            s.add(c.base)
        return s
    return rec(cat)

def theSameCats(a: Category, b: Category, c: Category) -> bool:
    s = set()
    def rec(cat):
        if cat.is_functor:
            rec(cat.left)
            rec(cat.right)
        else:
            s.add(cat.base)
        return s
    union = rec(a).union(rec(b),rec(c))
    return len(union) == 1




from typing import List
from depccg.tree import Tree
from depccg.printer.deriv import deriv_of
from parsed_reader import read_parsedstring, read_parsedtree

class CombinatorPairFinder(object):
    def __init__(self, path_list: List[str]):
        self.pathlist = path_list
        self.combinatorPairList = []

    def _traverse(self, tree: Tree):
        if tree.is_leaf == False:
            children = tree.children
            if len(children) == 1:
                self._traverse(children[0])
            else:
                self._traverse(children[0])
                self._traverse(children[1])
                if children[1].is_unary == False:
                    self.combinatorPairList.append([tree.op_symbol,
                                                    children[1].op_symbol,
                                                    str(tree.cat),
                                                    str(children[0].cat),
                                                    str(children[1].cat),
                                                    str(children[1].left_child.cat),
                                                    str(children[1].right_child.cat)])

    @staticmethod
    def create_combinatorPairList():
        self = CombinatorPairFinder(["/Users/kako/B4study-tools/ccgbank-20150216/devel/ja/left.txt",
                                    "/Users/kako/B4study-tools/ccgbank-20150216/test/ja/left.txt",
                                    "/Users/kako/B4study-tools/ccgbank-20150216/train/ja/left.txt",
                                    "/Users/kako/B4study-tools/BCCWJ-EyeTrack/data/parsed_featureless_nc/typeraised_leftbranched.txt"])

        seen = []
        for path in self.pathlist:
            trees = [tree for _, _, tree in read_parsedtree(path)]
            for tree in trees:
                self._traverse(tree)
            for i in self.combinatorPairList:
                if i not in seen:
                    seen.append(i)
        seen.sort()

        stack = []
        with open('/Users/kako/B4study-tools/BCCWJ-EyeTrack/data/CombinatorPair/integrated.txt', 'w') as f:
            for i in seen:
                print(f'op_symbol: {i[0]}, {i[1]}', file=f)
                #
                #             op_symbol: i[0], cat: i[2]
                #                  /              \
                #                 /                \
                #           cat: i[3]     op_symbol: i[1], cat: i[4]
                #                                /       \
                #                               /         \
                #                         cat: i[5]     cat: i[6]
                #
                stack.append('{' + i[0] + ' ' + i[2] + ' {' + i[3] + ' 1/1/_/_} {' + i[1] + ' ' + i[4] + ' {' + i[5] + ' 2/2/_/_} {' + i[6]+ ' 3/3/_/_}}}')
            f.write('\n')
            for i,j in enumerate(read_parsedstring(stack)):
                f.write(str(i))
                f.write('\n')
                f.write(deriv_of(j))
                f.write('\n')
CombinatorPairFinder.create_combinatorPairList()