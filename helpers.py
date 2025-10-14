from typing import Any, Callable, Iterable, Iterator


def rev_enumerate(it: list) -> Iterator:
    """Enumerates the object, but yields it in reverse order"""
    l = len(it)
    for i, x in enumerate(reversed(it)):
        yield (l-i-1, x)

def first_where(cond: Callable[[Any], bool], it: Iterable) -> Any | None:
    for el in it:
        if cond(el):
            return el
    return None

def scan(bin_f: Callable[[Any, Any], Any], it: Iterable, *, acc: Any) -> Iterator:
    """applies the binary function bin_f on an element and the previous result.<br>
    It accumulates the list stepwise.\n
    y = acc = bin_f(acc, x)\n
    Can for example be used to calculate the running sum"""
    for el in it:
        acc = bin_f(acc, el)
        yield acc

def nacs(bin_f: Callable[[Any, Any], Any], it: Iterable, *, x0: Any) -> Iterator:
    """applies the binary function bin_f on an element and the previous element<br>
    It de-accumulates the list stepwise.\n
    y = bin_f(prev_x, x)\n
    Can for example be used to calculate the differences leading to an inputed running sum"""
    prev_x = x0
    for x in it:
        y = bin_f(prev_x, x)
        prev_x = x
        yield y