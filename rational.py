
from math import gcd
from time import sleep
from typing import Iterator

Q = tuple[int, int]

def children(a: int, b: int) -> tuple[Q, Q]:
    assert gcd(a, b) == 1
    nom = a+b
    return (a, nom), (b, nom)

def child(a: int, b: int, right: bool) -> Q:
    assert gcd(a, b) == 1
    nom = a+b
    return (b, nom) if right else (a, nom)
    
def parent(a: int, b: int) -> tuple[Q, bool]:
    """returns: (parent, is_right_child)"""
    assert gcd(a, b) == 1
    if a == b == 1:
        return (1, 1), False
    x1 = a
    x2 = b-a
    is_right_child = x2<x1
    return ((x2, x1) if is_right_child else (x1, x2)), is_right_child

def history(a: int, b: int) -> Iterator[bool]:
    current = (a,b)
    while current != (1, 1):
        current, right = parent(*current)
        yield current, right

def q_to_num(a: int, b: int) -> int:
    assert a > 0
    assert b > 1
    assert gcd(a, b) == 1
    numstr = "0b1"+"".join(str(int(right)) for _, right in history(a, b))
    numstr = numstr[:-1] # last branch is always left
    return int(numstr, base=2)-1

def num_to_q(z: int) -> Q:
    bits = bin(z+1)[3:]
    current = (1, 2)
    for bit in bits[::-1]:
        current = child(*current, int(bit))
    return current

frac = (436, 757)


for z in range(1000):
    print(f"{z:>4} {num_to_q(z)}")