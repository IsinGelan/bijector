
from typing import ClassVar

from decorators import INFINITE_SIZE, BijStructure, derive, generate_bijection

from pairing_bijections import (
    ilist_to_i,
    ii_to_i,
    i_to_ii
    )




class N0(BijStructure):
    size: ClassVar[int] = INFINITE_SIZE
    n: int
    @classmethod
    def decode(cls, code):
        return cls(n=code)
    def encode(self):
        return self.n
    
n1_to_n0 = lambda n1: N0(n=n1.n-1)
n1_from_n0 = lambda n0: N1(n=n0.n+1)

@derive(N0, to_aux=n1_to_n0, from_aux=n1_from_n0)
class N1(BijStructure):
    n: int

z_to_n0 = lambda z: N0(n=2*abs(z.z) + z.z < 0)
z_from_n0 = lambda n0: Z(z=(-1 if (neg := n0.n % 2) else 1) * (n0.n - neg) // 2)

@derive(N0, to_aux=z_to_n0, from_aux=z_from_n0)
class Z(BijStructure):
    z: int

# IntAdapter = derive(int, Z, to_aux=lambda z: Z(z=z), from_aux=lambda z: z.z)

@generate_bijection
class IntPair(BijStructure):
    a: int
    b: int


class IntList(BijStructure):
    size: ClassVar[int] = INFINITE_SIZE

    elements: list[int]

    @classmethod
    def decode(cls, code: int):
        length, rest = i_to_ii(code)
    
    def encode(self):
        length = len(self.elements)
        el_code = ilist_to_i(self.elements)
        # TODO: give more priority to el_code
        return ii_to_i(length, el_code)
    

# @generate_bijection(exclude=["alphabet"])
class AlphabetString(BijStructure):
    """assumes the given alphabet and does not encode it."""
    alphabet: str
    string: str

tup = IntPair(a=1234567, b=9876)
print(z:=tup.encode())
print(IntPair.decode(z))