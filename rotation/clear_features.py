# A function which is an alternative to the method, 'clear_features'
# that eliminates the features assigned to each word.
# I made this code, because I can't use that method well...

from depccg.cat import Category, Functor, Atom
def clear_features(cat: Category) -> Category:
    if cat.is_functor:
        return Functor(
            clear_features(cat.left),
                cat.slash,
                clear_features(cat.right)
            )
    else:
        return Atom(cat.base)



# Wipe out features using regular expressions
# (Not related to the function defined above, just similar in its action)

if __name__ == '__main__':
    import re
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('FILE',
                        type=str,
                        help='path to the input text file of featured trees')

    args = parser.parse_args()
    FEATURES = re.compile(r'\[.+?\]')
    with open(args.FILE, 'r') as f:
        s = f.read()
        s = FEATURES.sub('',s)
        parent = str(Path(args.FILE).parent)
        file = str(Path(args.FILE).stem)
        output_path = parent + '/' + file + '_featureless.txt'
        with open(output_path, 'w') as g:
            g.write(s)
