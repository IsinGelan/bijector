
from typing import ClassVar
from bij_type import INFINITE_SIZE, BijType
from decorators import derive, generate_bijection
from pairing_bijections import i_to_ii, i_to_ilist, ii_to_i, ilist_to_i


class N0(BijType):
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
class N1(BijType):
    n: int

z_to_n0 = lambda z: N0(n=2*abs(z.z) + z.z < 0)
z_from_n0 = lambda n0: Z(z=(-1 if (neg := n0.n % 2) else 1) * (n0.n - neg) // 2)

@derive(N0, to_aux=z_to_n0, from_aux=z_from_n0)
class Z(BijType):
    z: int

@generate_bijection
class IntPair(BijType):
    a: int
    b: int

class IntList(BijType):
    size: ClassVar[int] = INFINITE_SIZE

    elements: list[int]

    @classmethod
    def decode(cls, code: int):
        length, rest = i_to_ii(code)
        lis = i_to_ilist(rest, length=length)
        return cls(lis)
    
    def encode(self):
        length = len(self.elements)
        el_code = ilist_to_i(self.elements)
        # TODO: give more priority to el_code
        return ii_to_i(length, el_code)