import argparse
import numpy as np
import pandas as pd
from nodecount import CombinatorCount, RevealCombinatorCount
from parsed_reader import read_parsedtree


def cc_make_csv(df, OUTPUT_PATH: str) -> None:
    word2phrase = pd.read_csv("/Users/kako/B4study-tools/BCCWJ-EyeTrack/data/parsed_featureless/NodeCount/word2phrase.csv", header=None, names=['n'])
    count = np.zeros(4, dtype=np.int64)
    stack = []
    no = 0
    for i in word2phrase.n:
        while i >= no:
            count += df.iloc[no]
            no += 1
        stack.append(count)
        count = np.zeros(4, dtype=np.int64)
    df = pd.DataFrame(stack)
    df.columns = ['binary', 'forward', 'backward', 'typeraise']
    df = df.reset_index(drop=True)
    df = pd.concat([pd.concat([df[:438]]*12),pd.concat([df[438:818]]*12),pd.concat([df[818:1137]]*12),pd.concat([df[1137:]]*12)])
    df = df.reset_index(drop=True)
    df.to_csv(OUTPUT_PATH, index=False)

def rc_make_csv(df, OUTPUT_PATH: str) -> None:
    word2phrase = pd.read_csv("/Users/kako/B4study-tools/BCCWJ-EyeTrack/data/parsed_featureless/NodeCount/word2phrase.csv", header=None, names=['n'])
    count = np.zeros(2, dtype=np.int64)
    stack = []
    no = 0
    for i in word2phrase.n:
        while i >= no:
            count += df.iloc[no]
            no += 1
        stack.append(count)
        count = np.zeros(2, dtype=np.int64)
    df = pd.DataFrame(stack)
    df.columns = ['reveal', 'rotation']
    df = df.reset_index(drop=True)
    df = pd.concat([pd.concat([df[:438]]*12),pd.concat([df[438:818]]*12),pd.concat([df[818:1137]]*12),pd.concat([df[1137:]]*12)])
    df = df.reset_index(drop=True)
    df.to_csv(OUTPUT_PATH, index=False)


if __name__ == '__main__':
    RIGHT = "/Users/kako/B4study-tools/BCCWJ-EyeTrack/data/parsed_featureless/text/right.txt"
    TYPERAISE = "/Users/kako/B4study-tools/BCCWJ-EyeTrack/data/parsed_featureless/text/typeraised.txt"
    LEFT = "/Users/kako/B4study-tools/BCCWJ-EyeTrack/data/parsed_featureless/text/left.txt"

    parser = argparse.ArgumentParser()
    parser.add_argument('--output',
                        choices=['cc', 'rc'],
                        default='cc')

    args = parser.parse_args()
    if args.output == 'rc':
        trees = [tree for _, _, tree in read_parsedtree(LEFT)]
        df = RevealCombinatorCount.make_data_frame(trees)
        rc_make_csv(df, "/Users/kako/B4study-tools/BCCWJ-EyeTrack/data/parsed_featureless/NodeCount/reveal.csv")

    else:
        trees = [tree for _, _, tree in read_parsedtree(RIGHT)]
        df = CombinatorCount.make_data_frame(trees)
        cc_make_csv(df, "/Users/kako/B4study-tools/BCCWJ-EyeTrack/data/parsed_featureless/NodeCount/right_combinators.csv")

        trees = [tree for _, _, tree in read_parsedtree(TYPERAISE)]
        df = CombinatorCount.make_data_frame(trees)
        cc_make_csv(df, "/Users/kako/B4study-tools/BCCWJ-EyeTrack/data/parsed_featureless/NodeCount/typeraised_combinators.csv")

        trees = [tree for _, _, tree in read_parsedtree(LEFT)]
        df = CombinatorCount.make_data_frame(trees)
        cc_make_csv(df, "/Users/kako/B4study-tools/BCCWJ-EyeTrack/data/parsed_featureless/NodeCount/left_combinators.csv")

