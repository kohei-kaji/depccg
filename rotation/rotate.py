# parsed txt(right-branch) -> /text/right.txt
#                             /text/typeraised.txt
#                             /text/left.txt
#                             /NodeCount/right.csv
#                             /NodeCount/typeraised.csv
#                             /NodeCount/left.csv
#
# ccgbank directory -> /devel/ja/right.txt
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('PATH', type=Path, help='path to the parsed text file or ccgbank directory')
    parser.add_argument('--input',
                        help="Choose 'ccgbank' or 'parsed'. The latter requires a text file of Japanese ccgbank format without information about dependencies.",
                        choices=['ccgbank', 'parsed'],
                        default='ccgbank')

    args = parser.parse_args()

    if args.input == 'parsed':
        PARENT_DIR = Path(args.PATH).parent
        TEXT_DIR = PARENT_DIR / 'text'
        TEXT_DIR.mkdir(parents=True, exist_ok=True)
        NC_DIR = PARENT_DIR / 'NodeCount'
        NC_DIR.mkdir(parents=True, exist_ok=True)

        trees = [tree for _, _, tree in read_parsedtree(args.PATH)]
        TEXT_RIGHT = TEXT_DIR / 'right.txt'
        trees_to_ja(TEXT_RIGHT, trees)
        NC_RIGHT = NC_DIR / 'right.csv'
        nodecount(NC_RIGHT, trees)

        typeraised_trees = [TypeRaise.apply_typeraise(tree) for tree in trees]
        TEXT_TR = TEXT_DIR / 'typeraised.txt'
        trees_to_ja(TEXT_TR, typeraised_trees)
        NC_TR = NC_DIR / 'typeraised.csv'
        nodecount(NC_TR, typeraised_trees)

        leftbranched_trees = [TreeRotation.rotate(tree) for tree in typeraised_trees]
        TEXT_LEFT = TEXT_DIR / 'left.txt'
        trees_to_ja(TEXT_LEFT, leftbranched_trees)
        NC_LEFT = NC_DIR / 'left.csv'
        nodecount(NC_LEFT, leftbranched_trees)


    else:
        PARENT_DIR = Path(args.PATH)

        devel = PARENT_DIR / 'devel.ccgbank'
        test = PARENT_DIR / 'test.ccgbank'
        train = PARENT_DIR / 'train.ccgbank'

        DEVEL_JA = PARENT_DIR/ 'devel/ja/'
        DEVEL_AUTO = PARENT_DIR / 'devel/auto/'
        TEST_JA = PARENT_DIR / 'test/ja/'
        TEST_AUTO = PARENT_DIR / 'test/auto/'
        TRAIN_JA = PARENT_DIR / 'train/ja/'
        TRAIN_AUTO = PARENT_DIR / 'train/auto/'

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


if __name__ == '__main__':
    main()
