# find_verb.pyで作った名詞句・動詞句list（verb_list）をもとに、NPのtype-raised dict (trdict) を作る。
# trdictをもとに、typeraise.pyで名詞句をtyperaiseさせる予定。

import argparse
import logging
from pathlib import Path
from typing import Dict
# import json

from depccg.cat import Category, Functor
from depccg.unification import Unification

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

class MakeTypeRaiseDict(object):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.dict = {}
        self.one_arg = r"S[mod=X1,form=X2,fin=X3]/(S[mod=X1,form=X2,fin=X3]\NP[case=X1,mod=X2,fin=X3])"
        self.two_args = r"(S[mod=X1,form=X2,fin=X3]\NP[case=X1,mod=X2,fin=X3])/((S[mod=X1,form=X2,fin=X3]\NP[case=X1,mod=X2,fin=X3])\NP[case=X1,mod=X2,fin=X3])"
        self.three_args = r"((S[mod=X1,form=X2,fin=X3]\NP[case=X1,mod=X2,fin=X3])\NP[case=X1,mod=X2,fin=X3])/(((S[mod=X1,form=X2,fin=X3]\NP[case=X1,mod=X2,fin=X3])\NP[case=X1,mod=X2,fin=X3])\NP[case=X1,mod=X2,fin=X3])"
        self.four_args = r"(((S[mod=X1,form=X2,fin=X3]\NP[case=X1,mod=X2,fin=X3])\NP[case=X1,mod=X2,fin=X3])\NP[case=X1,mod=X2,fin=X3])/((((S[mod=X1,form=X2,fin=X3]\NP[case=X1,mod=X2,fin=X3])\NP[case=X1,mod=X2,fin=X3])\NP[case=X1,mod=X2,fin=X3])\NP[case=X1,mod=X2,fin=X3])"
    
    def _typeraise(self, l: str, r: str) -> Dict[str, str]:
        left = Category.parse(l)
        right = Category.parse(r)
    
        if right.nargs == 1:
            self.dict[r] = self.one_arg
        elif right.nargs == 2:
            self.dict[r] = self.two_args
        elif right.nargs == 3:
            self.dict[r] = self.three_args
        elif right.nargs == 4:
            self.dict[r] = self.four_args
        else:
            raise Exception
        
        # 単純に考えると、
        # X -> T/(T\X) (>T)
        
        # Tの素性はvariableにしたいので、
        # VPはS\NP, S\NP\NPの形しかないのであれば、
        # if right.nargs == 1:
        # elif right.nargs == 2:
        
        # より安全なのは、right.leftのfeatureにaccessして、
        # すべて[case=X1,mod=X2,fin=X3]に変換する
        # S[mod=X1,form=X2,fin=X3]
        # NP[case=ga,mod=X1,fin=X2], NP[case=o,mod=X1,fin=X2]
        # NP[case=ga] -> S[mod=X1,form=X2,fin=X3]/(S[mod=X1,form=X2,fin=X3]\NP[case=ga,mod=X1,fin=X2])
        # NP[case=o] -> (S[mod=X1,form=X2,fin=X3]\NP[case=X1,mod=X2,fin=X3])/(S[mod=X1,form=X2,fin=X3]\NP[case=X1,mod=X2,fin=X3]\NP[case=o,mod=X1,fin=X2])
        
        # T = str(right.left)
        # X = str(left)
        # typeraise = T + '/(' + T + '\\' + X + ')'
        # self.dict[typeraise] = X
        
        # or
        # T = str(right.left)
        # X = str(right)
        # typeraise = T + '/' + X
        # uni = Unification('a/b', 'b')
        # if uni(typeraise, right):
        #   return typeraise
        # else:
        # raise Expection
    
        
    @staticmethod
    def _write(dct, filename):
        with open(filename, 'w') as f:
            logger.info(f'writing to {f.name}')
            for key, value in dct.items():
                print(f'{key} {str(value)}', file=f)


    @staticmethod
    def make_trdict(args):
        self = MakeTypeRaiseDict(args.PATH)

        with open(self.filepath, 'r') as f:
            for line in f:
                lst = line.split()
                self._typeraise(lst[0], lst[1])
        
        cwd = Path.cwd()
        self._write(self.dict, cwd / 'trdict.txt')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH',
                        type=Path,
                        help='path to the txt file of a verb list')
    
    args = parser.parse_args()
    MakeTypeRaiseDict.make_trdict(args)
    