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
from typeraise import TypeRaise
from tree_rotation import TreeRotation

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

    if args.input == 'parsed':
        directory_name = parent + '/' + file + '_nc'
        os.makedirs(directory_name, exist_ok=True)

        trees = [tree for _, _, tree in read_parsedtree(args.FILE)]
        nc_name = directory_name + '/right.csv'
        nodecount(nc_name, trees)

        typeraised_trees = [TypeRaise.apply_typeraise(tree) for tree in trees]
        tr_nc_name = directory_name + '/typeraised.csv'
        nodecount(tr_nc_name, typeraised_trees)

        leftbranched_trees = [TreeRotation.rotate(tree) for tree in trees]
        lb_nd_name = directory_name + '/leftbranched.csv'
        nodecount(lb_nd_name, leftbranched_trees)

        shutil.move(args.FILE, directory_name)

    else:
        directory_name = parent + '/' + file + '_auto'
        os.makedirs(directory_name, exist_ok=True)

        trees = [tree for _, _, tree in read_ccgbank(args.FILE)]
        auto_name = directory_name + '/right'
        ja_to_auto(auto_name, trees)

        typeraised_trees = [TypeRaise.apply_typeraise(tree) for tree in trees]
        tr_auto_name = directory_name + '/typeraised'
        ja_to_auto(tr_auto_name, typeraised_trees)

        leftbranched_trees = [TreeRotation.rotate(tree) for tree in trees]
        lb_auto_name = directory_name + '/leftbranched'
        ja_to_auto(lb_auto_name, leftbranched_trees)
