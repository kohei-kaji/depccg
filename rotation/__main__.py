# input_txt(parsed) -> nodecount
#                   -> (typeraise) -> nodecount
#                                  -> (leftbranch) -> nodecount
# input_txt(ccgbank) -> auto
#                    -> (typeraise) -> auto
#                                   -> (leftbranch) -> auto

import os
import shutil
import argparse
from pathlib import Path

from depccg.tools.ja.reader import read_ccgbank

from converter import ja_to_auto
from nodecount import nodecount
from reader import read_parsedtree
from rotation import TreeRotation
from typeraise import ApplyTypeRaise

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('FILE', type=str, help='path to the input text file')
    parser.add_argument('--input',
                        help="Choose 'CCGBank' or 'parsed'. The latter requires a text file of Japanese CCGBank format parsed by depccg.",
                        choices=['CCGBank', 'parsed'],
                        default='CCGBank')
    
    args = parser.parse_args()
    parent = str(Path(args.FILE).parent)
    file = str(Path(args.FILE).stem)
    directory_name = parent + '/' + file
    
    os.mkdir(directory_name)

    if args.input == 'parsed':
        trees = [tree for _, _, tree in read_parsedtree(args.FILE)]
        nd_name = directory_name + '_nodecount.csv'
        nodecount(nd_name, trees)
        
        typeraised_trees = [ApplyTypeRaise.apply_typeraise(tree) for tree in trees]
        tr_nd_name = directory_name + 'typeraised_nodecount.csv'
        nodecount(tr_nd_name, typeraised_trees)
        
        treerotation = TreeRotation()
        
        
        

                
    else:
        trees = [tree for _, _, tree in read_ccgbank(args.FILE)]
        auto_name = directory_name + '_auto'
        
        ja_to_auto(auto_name, trees)

    
    shutil.move(args.FILE, new_directory)
