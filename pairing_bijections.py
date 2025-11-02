
from itertools import chain
from math import prod, sqrt, comb as binomial
from typing import Iterable, Iterator

from helpers import first_where, nacs, rev_enumerate, scan

# == Endliche Paarungsfunktionen ==
def ff_to_f(x: int, y: int, *, xmax: int, ymax: int) -> int:
    assert x < xmax
    assert y < ymax
    return ymax * x + y

def f_to_ff(z: int, *, xmax: int, ymax: int) -> tuple[int, int]:
    assert z < xmax * ymax
    pass

def flist_to_f(xs: list[int], *, maxes: list[int]) -> int:
    assert len(xs) == len(maxes)
    assert all((x < maxx) for x, maxx in zip(xs, maxes))

    multipliers = scan(lambda a,b: a*b, maxes, acc=1, yield_start=True)
    return sum(x * mult for x, mult in zip(xs, multipliers))

def f_to_flist(z: int, *, length: int, maxes: Iterable[int]) -> Iterator[int]:
    """without infinite (arbitrary size) remainder! 
    If the input overflows the last index maximum, an error will be raised\n
    It is thus suggested to use an infinite Iterator for maxes"""
    for m, _ in zip(maxes, range(length)):
        res, z = divmod(z, m)
        yield res



# == Unendliche Paarungfunktionen ==
def pair_diagonal(x: int, y: int) -> int:
    """Pairing function by Cantor (compares to the Manhattan metric)"""
    return (x+y)*(x+y-1) // 2 + y

def unpair_diagonal(z: int) -> tuple[int, int]:
    """Unpairing function by Cantor"""
    x_plus_y = 0.5 + sqrt(2*z + 0.25)
    xpy = int(x_plus_y)
    y = z - xpy*(xpy-1) // 2
    x = xpy - y
    return x, y

def pair_block(x: int, y: int) -> int:
    """compares to Max-Metric"""
    m = max(x, y)
    rest = x if y == m else m + y + 1
    return m*m + rest

def unpair_block(z: int) -> int:
    m = int(sqrt(z))
    rest = z - m*m
    x, y = (rest, m) if rest <= m else (m, rest-m-1)
    return x, y


# ================================
def find_m(k: int, n: int) -> int:
    # TODO: optimize search strategy
    for m in range(k-1, k+n+1):
        b = binomial(m, k)
        if b > n:
            return m

def cantor_list_iter(kk: int, n: int):
    for k in range(kk, 0, -1):
        m = find_m(k, n)
        d = m-1
        n -= binomial(d, k)
        yield d


# ================================
def multi_oblique(xs: list[int]) -> int:
    """for a metric where a block of <= n is shaped like n * (n+1) * ... * (n+d-1)<br>
    e.g. for d = 3, if n = 5, the block is 5 * 6 * 7 large\n
    Vorteil: alle Randkörper sind gleich groß, Zahlengewichtung über alle Indizes fast gleich groß"""
    d = len(xs)
    m = max(x-i for i, x in enumerate(xs))
    start = prod(m+i for i in range(d))
    
    # Differenz zwischen Blockgrößen müsste immer d * prod(m+i for i in range(d-1)) sein
    # also für d = 3, m = 5: 3 * (5 * 6) 
    # wir nennen den Teilrandkörper (der hier Größe 5 * 6 hat) pane
    bounds = [m+i+1 for i in range(d-1)]
    pane_size = prod(bounds) # = start // (m+d-1)

    # find which pane the pos is in
    pane_normal_ind, _ = first_where(lambda ix: ix[1] == m + ix[0], rev_enumerate(xs))
    pane_coords = [x for i, x in enumerate(xs) if i != pane_normal_ind]

    pane_z = flist_to_f(pane_coords, maxes=bounds)

    z = start + ff_to_f(pane_normal_ind, pane_z, xmax=d, ymax=pane_size)
    return z

def unmulti_oblique(z: int, *, length: int) -> list[int]:
    # Schwierig!
    pass

def unmulti_recursive(z: int, *, number: int) -> Iterator[int]:
    assert number > 0
    for _ in range(number - 1):
        el, z = i_to_ii(z)
        yield el
    yield z

def multi_cantor(xs: list[int]) -> int:
    xs_acc = 0
    res_acc = 0
    for i, x in enumerate(xs, start=1):
        xs_acc += x
        res_acc += binomial(xs_acc + i - 1, i)
    return res_acc

def unmulti_cantor(z: int, *, length: int):
    xs = list(cantor_list_iter(length, z))
    return iset_to_ilist(xs[::-1])


# ================================
# == Einfache Funktionen =========
def fi_to_i(x: int, y: int, *, m: int) -> int:
    """x[0...m-1], y[inf]<br>
    returns z(x,y)[inf]"""
    assert 0 <= x < m
    return m*y + x

def ii_to_i(x: int, y: int) -> int:
    """x[inf], y[inf]<br>
    returns z(x,y)[inf]"""
    return pair_block(x, y)

def i_to_fi(z: int, *, m: int) -> tuple[int, int]:
    """m: max for the fin number<br>
    returns: num[0...m-1], rest[inf]"""
    num, rest = divmod(z, m)
    return rest, num

def i_to_ii(z: int) -> tuple[int, int]:
    """returns: num[inf], rest[inf]"""
    return unpair_block(z)

def ilist_to_i(lis: list[int]) -> int:
    return multi_cantor(lis)

def i_to_ilist(z: int, *, length: int) -> list[int]:
    """uses up the number (gives no rest)"""
    return unmulti_cantor(z=z, length=length)

def iset_to_ilist(s: list[int]) -> list[int]:
    """set as finite list in sorted order"""
    return list(nacs(lambda prev_x, x: x-prev_x-1, s, x0=-1))

def ilist_to_iset(lis: list[int]) -> list[int]:
    """set as finite list in sorted order"""
    return list(scan(lambda a, x: a+x+1, lis, acc=-1))

# TODO: Introduce pairing priority into the functions
# TODO: (so that one variable gets more updates for the same number)

# std_config = BijConfig(
#     Bijection(pro=)
# )

def test_cantor(zmax = 10000000, length = 3):
    for z in range(zmax):
        lis = unmulti_cantor(z, length=length)
        znew = multi_cantor(lis)
        if z == znew:
            continue
        raise ValueError("The cantor ranking function does not agree with its inverse\n"
                         f"at z = {z}  f^-1(f(z)) = {znew}")
