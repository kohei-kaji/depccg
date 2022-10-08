# parsed txt(right-branch) -> /text/right.txt
#                             /text/typeraised.txt
#                             /text/left.txt
#                             /NodeCount/right.csv
#                             /NodeCount/typeraised.csv
#                             /NodeCount/left.csv
#
# CCGBank directory -> /devel/ja/right.txt
#                      /devel/ja/typeraised.txt
#                      /devel/ja/left.txt
#                      /devel/auto/right.txt
#                      /devel/auto/typeraised.txt
#                      /devel/auto/left.txt
#
#                      /test/ja/right.txt
#                      /test/ja/typeraised.txt
#                      /test/ja/left.txt
#                      /test/auto/right.txt
#                      /test/auto/typeraised.txt
#                      /test/auto/left.txt
#
#                      /train/ja/right.txt
#                      /train/ja/typeraised.txt
#                      /train/ja/left.txt
#                      /train/auto/right.txt
#                      /train/auto/typeraised.txt
#                      /train/auto/left.txt


import argparse
from pathlib import Path

from converter import trees_to_auto, trees_to_ja
from nodecount import nodecount
from parsed_reader import read_parsedtree
from ccgbank_reader import read_ccgbank
from typeraise import TypeRaise
from tree_rotation import TreeRotation


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH', type=str, help='path to the parsed text file or CCGBank directory')
    parser.add_argument('--input',
                        help="Choose 'CCGBank' or 'parsed'. The latter requires a text file of Japanese CCGBank format parsed by depccg.",
                        choices=['CCGBank', 'parsed'],
                        default='CCGBank')

    args = parser.parse_args()

    if args.input == 'parsed':
        parent = Path(args.PATH).parent
        text_dir = parent / 'text'
        text_dir.mkdir()
        nc_dir = parent / 'NodeCount'
        nc_dir.mkdir()

        trees = [tree for _, _, tree in read_parsedtree(args.PATH)]
        text_right = text_dir / 'right.txt'
        trees_to_ja(text_right, trees)
        nc_right = nc_dir / 'right.csv'
        nodecount(nc_right, trees)

        typeraised_trees = [TypeRaise.apply_typeraise(tree) for tree in trees]
        text_tr = text_dir / 'typeraised.txt'
        trees_to_ja(text_tr, typeraised_trees)
        nc_tr = nc_dir / 'typeraised.csv'
        nodecount(nc_tr, typeraised_trees)

        leftbranched_trees = [TreeRotation.rotate(tree) for tree in typeraised_trees]
        text_left = text_dir / 'left.txt'
        trees_to_ja(text_left, leftbranched_trees)
        nc_left = nc_dir / 'left.csv'
        nodecount(nc_left, leftbranched_trees)


    else:
        parent = Path(args.PATH)

        devel = parent / 'devel.ccgbank'
        test = parent / 'test.ccgbank'
        train = parent / 'train.ccgbank'

        DEVEL_JA = parent / 'devel/ja/'
        DEVEL_AUTO = parent / 'devel/auto/'
        TEST_JA = parent / 'test/ja/'
        TEST_AUTO = parent / 'test/auto/'
        TRAIN_JA = parent / 'train/ja/'
        TRAIN_AUTO = parent / 'train/auto/'

        DEVEL_JA.mkdir(parents=True)
        DEVEL_AUTO.mkdir()
        TEST_JA.mkdir(parents=True)
        TEST_AUTO.mkdir()
        TRAIN_JA.mkdir(parents=True)
        TRAIN_AUTO.mkdir()


        trees = [tree for _, _, tree in read_ccgbank(str(devel))]
        trees_to_ja(str(DEVEL_JA/'right.txt'), trees)
        trees_to_auto(str(DEVEL_AUTO/'right.txt'), trees)
        trees = [TypeRaise.apply_typeraise(tree) for tree in trees]
        trees_to_ja(str(DEVEL_JA/'typeraised.txt'), trees)
        trees_to_auto(str(DEVEL_AUTO/'typeraised.txt'), trees)
        trees = [TreeRotation.rotate(tree) for tree in trees]
        trees_to_ja(str(DEVEL_JA/'left.txt'), trees)
        trees_to_auto(str(DEVEL_AUTO/'left.txt'), trees)

        trees = [tree for _, _, tree in read_ccgbank(str(test))]
        trees_to_ja(str(TEST_JA/'right.txt'), trees)
        trees_to_auto(str(TEST_AUTO/'right.txt'), trees)
        trees = [TypeRaise.apply_typeraise(tree) for tree in trees]
        trees_to_ja(str(TEST_JA/'typeraised.txt'), trees)
        trees_to_auto(str(TEST_AUTO/'typeraised.txt'), trees)
        trees = [TreeRotation.rotate(tree) for tree in trees]
        trees_to_ja(str(TEST_JA/'left.txt'), trees)
        trees_to_auto(str(TEST_AUTO/'left.txt'), trees)

        trees = [tree for _, _, tree in read_ccgbank(str(train))]
        trees_to_ja(str(TRAIN_JA/'right.txt'), trees)
        trees_to_auto(str(TRAIN_AUTO/'right.txt'), trees)
        trees = [TypeRaise.apply_typeraise(tree) for tree in trees]
        trees_to_ja(str(TRAIN_JA/'typeraised.txt'), trees)
        trees_to_auto(str(TRAIN_AUTO/'typeraised.txt'), trees)
        trees = [TreeRotation.rotate(tree) for tree in trees]
        trees_to_ja(str(TRAIN_JA/'left.txt'), trees)
        trees_to_auto(str(TRAIN_AUTO/'left.txt'), trees)
