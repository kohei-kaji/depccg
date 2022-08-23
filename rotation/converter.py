import argparse
from depccg.tools.ja.reader import read_ccgbank
from depccg.printer.html import _MATHML_MAIN, _mathml_subtree
from depccg.printer.auto import auto_of
from pathlib import Path

def ja_to_auto(input_path: str, output_path: str):
    """rewrite Japanese CCGBank with English CCGBank format.

    Args:
        filepath (str): file name string

    Results:
        text file which contains Japanese CCGBank of the English CCGBank format
    """
    with open(output_path, 'w') as f:
        trees = [tree for _, _, tree in read_ccgbank(input_path)]
        for tree in trees:
            f.write(auto_of(tree))
            f.write('\n')

def ja_to_html(input_path: str, output_path: str):
    """rewrite Japanese CCGBank with the html format.

    Args:
        filepath (str): file name string

    Results:
        str: html format (refer to ./depccg/printer/html.py)
    """
    with open(output_path, 'w') as f:
        trees = [tree for _, _, tree in read_ccgbank(input_path)]
        for tree in trees:
            result = ''
            words = tree.word
            result += f'<p>{words}</p>'
            tree_str = tree if isinstance(tree, str) else _mathml_subtree(tree)
            result += f'<math xmlns="http://www.w3.org/1998/Math/MathML">{tree_str}</math>'
            f.write(_MATHML_MAIN.format(result))
            f.write('\n')
        
   
if __name__ == '__main__':  
    parser = argparse.ArgumentParser()
    parser.add_argument('INPUT', type=str, help='path to the input text file')
    parser.add_argument('--format',
                        choices=['html', 'auto'],
                        default='html')
    args = parser.parse_args()
    parent = str(Path(args.INPUT).parent)
    file = str(Path(args.INPUT).stem)
    
    if args.format == 'auto':    
        output_name = parent + '/' + file + '_converted'
        ja_to_auto(args.INPUT, output_name)
    else:
        output_name = parent + '/' + file + '.html'
        ja_to_html(args.INPUT, output_name)
