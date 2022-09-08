# Because I cannot use the method of Atom and Functor, 'clear_features' well...
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
