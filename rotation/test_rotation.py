from typeraise import TypeRaise
from tree_rotation import TreeRotation
from parsed_reader import read_parsedstring

from depccg.printer.deriv import deriv_of

if __name__ == '__main__':
    inputs = [r'{> S {S/S Today/Today/_/_} {< S {NP Mary/Mary/_/_} {> S\NP {(S\NP)/NP ate/ate/_/_} {NP apples/apples/_/_}}}}',
              r'{>Bx1 S/NP {S/S 1/1/_/_} {>Bx1 S\NP {ADV0 S/S {< S {> S {S/S 2/2/_/_} {S 3/3/_/_}} {S\S 4/4/_/_}}} {S\NP 5/5/_/_}}}',
              r'{> S {ADV0 S/S {S 1/1/_/_}} {< S {NP 2/2/_/_} {S\NP 3/3/_/_}}}',
              r'{> S {S/S 1/1/_/_} {< S {NP 2/2/_/_} {<B1 S\NP {S\NP 3/3/_/_} {S\S 4/4/_/_}}}}',
              r'{> S {> S/S {(S/S)/(S\NP) 1/1/_/_} {> S\NP {(S\NP)/NP 2/2/_/_} {NP 3/3/_/_}}} {> S {S/NP 4/4/_/_} {NP 5/5/_/_}}}',
              r'{< NP {NP 1/1/_/_} {<B1 NP\NP {NP\NP 2/2/_/_} {NP\NP 3/3/_/_}}}',
              r'{> NP {>B NP/NP {NP/NP 池田/池田/_/_} {>B NP/NP {NP/NP 弘子/弘子/_/_} {NP/NP 先生/先生/_/_}}} {< NP {> NP {NP/NP （/（/_/_} {> NP {NP/NP ７/７/_/_} {NP ５/５/_/_}}} {NP\NP ）/）/_/_}}}}']

    for i,j in enumerate(read_parsedstring(inputs)):
        print(i)
        print("original tree")
        print(deriv_of(j))
        print("type-raising")
        typeraise = TypeRaise.apply_typeraise(j)
        print(deriv_of(typeraise))
        print("after rotation")
        print(deriv_of(TreeRotation.rotate(typeraise)))
        print()
