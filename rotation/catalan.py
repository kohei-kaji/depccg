"""This calculates the Catalan numbers.
Usage:

for example,
    $ python catalan.py 1 2 3 4 5 6 7 8 9 10
    -> [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862]

- Give a list of integers n as command-line arguments, separated by spaces, not by any punctuations,
- and then, the Catalan numbers of n-1 are outputted.
- Do not put the list in parentheses or brackets.
- The outputs mean that the maximum patterns of spurious ambiguity which the string of n words can derive.
"""


import argparse
import math


def catalan(ns: list[int]) -> list[int]:
    return [int(math.comb(2 * (n - 1), (n - 1)) / n) for n in ns]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("INPUT", nargs="*", type=int, help="a list of integers")
    args = parser.parse_args()

    print(catalan(args.INPUT))
