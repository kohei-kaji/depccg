from typeraise import TypeRaise
from parsed_reader import read_parsedstring

from depccg.printer.deriv import deriv_of

if __name__ == '__main__':
    inputs = [r'{> S {S/S 1/1/_/_} {< S {NP 2/2/_/_} {> S\NP {(S\NP)/NP 3/3/_/_} {NP 4/4/_/_}}}}',
              r'{> NP {NP/NP 1/1/_/_} {< NP {S 2/2/_/_} {NP\S 3/3/_/_}}}',
              r'{> NP {NP/NP 1/1/_/_} {< NP {NP 2/2/_/_} {NP\NP 3/3/_/_}}}',
              r'{>B NP/NP {NP/NP 1/1/_/_} {< NP/NP {NP/NP 2/2/_/_} {(NP/NP)\(NP/NP) 3/3/_/_}}}',
              r'{>B S/S {S/S 1/1/_/_} {< S/S {NP 2/2/_/_} {(S/S)\NP 3/3/_/_}}}']

    answers = [r'{> S {S/S 1/1/_/_} {> S {>T S/(S\NP) {NP 2/2/_/_}} {> S\NP {(S\NP)/NP 3/3/_/_} {NP 4/4/_/_}}}}',
               r'{> NP {NP/NP 1/1/_/_} {> NP {>T NP/(NP\S) {S 2/2/_/_}} {NP\S 3/3/_/_}}}',
               r'{> NP {NP/NP 1/1/_/_} {> NP {>T NP/(NP\NP) {NP 2/2/_/_}} {NP\NP 3/3/_/_}}}',
               r'{>B NP/NP {NP/NP 1/1/_/_} {> NP/NP {>T (NP/NP)/((NP\NP)\(NP\NP)) {NP/NP 2/2/_/_}} {(NP/NP)\(NP/NP) 3/3/_/_}}}',
               r'{>B S/S {S/S 1/1/_/_} {> S/S {>T (S/S)/((S/S)\NP) {NP 2/2/_/_}} {(S/S)\NP 3/3/_/_}}}']
    answers = read_parsedstring(answers)

    for i,j in enumerate(read_parsedstring(inputs)):
        print(i)
        print("original tree")
        print(deriv_of(j))
        print("after type-raise")
        print(deriv_of(TypeRaise.apply_typeraise(j)))
        print("answer")
        print(deriv_of(answers[i]))
        print()
