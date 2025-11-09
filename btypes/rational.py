
from math import gcd
from typing import ClassVar, Iterator, Self

from decorators import INFINITE_SIZE, BijType
from pairing_bijections import fi_to_i, i_to_fi

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

class Q(BijType):
    size: ClassVar[int] = INFINITE_SIZE
    a: int
    b: int

    def model_post_init(self, context):
        self.validate()
        return super().model_post_init(context)

    def validate(self):
        if self.b == 0:
            raise ZeroDivisionError(
                "fraction can't be a division by zero!\n"
                f"Got {self.a}/{self.b}")
        if gcd(self.a, self.b) != 1:
            raise ValueError(
                "Q requires irreducible fraction as input!\n"
                f"Got {self.a}/{self.b}")
        
        self.b = 1 if self.a == 0 else self.b

    @classmethod
    def from_int(cls, num: int) -> Self:
        return Q(a=num, b=1)
    
    def __int__(self) -> int:
        return self.a // self.b
    def __float__(self) -> float:
        return self.a / self.b
    
    def __str__(self):
        return f"{self.a}/{self.b}"
    def __repr__(self):
        return f"{self.a}/{self.b}"

    def encode(self):
        """0: 0/1\n
        1,2: 1/1, -1/1\n
        3,...: a/b, b/a, -a/b, -b/a """
        neg = (self.a < 0) ^ (self.b < 0)
        a = abs(self.a)
        b = abs(self.b)

        if a == 0:
            return 0
        if a == b == 1:
            return 1 + neg

        a, b, hi_div_lo = (a, b, False) if a < b else (b, a, True)
        mode = 2*neg + hi_div_lo
        num  = q_to_num(a, b)
        return 3 + fi_to_i(mode, num, m=4)
    
    @classmethod
    def decode(cls, c: int):
        match c:
            case 0: return cls(a=0,b=1)
            case 1: return cls(a=1,b=1)
            case 2: return cls(a=-1,b=1)
        c -= 3
        mode, num = i_to_fi(c, m=4)
        neg, hi_div_lo = divmod(mode, 2)
        a, b = num_to_q(num)
        a, b = (b, a) if hi_div_lo else (a, b)
        return cls(a=(-1 if neg else 1) * a, b=b)
    
    @staticmethod
    def reduced_tuple(a: int, b: int) -> tuple[int, int]:
        g = gcd(a, b)
        return (a//g, b//g)
    
    @classmethod
    def reduced(cls, a: int, b: int) -> Self:
        g = gcd(a, b)
        return cls(a=a//g, b=b//g)

    def __neg__(self) -> Self:
        return Q(-self.a, self.b)

    def __add__(self, other: Self) -> Self:
        divisor = self.b * other.b
        return Q.reduced(self.a * other.b + other.a * self.b, divisor)
        
    def __sub__(self, other: Self) -> Self:
        return self + (- other)
    
    def __mul__(self, other: Self) -> Self:
        return Q.reduced(self.a * other.a, self.b * other.b)

    def __div__(self, other: Self) -> Self:
        return Q.reduced(self.a * other.b, self.b * other.a)
    
    def __mod__(self, other: Self | int) -> Self:
        o = Q(a=other, b=1) if isinstance(other, int) else other
        divisor = self.b * o.b
        rest = (self.a * o.b) % (o.a * self.b)
        return Q.reduced(rest, divisor)
    
    def __divmod__(self, other: Self | int) -> tuple[Self, Self]:
        o = Q(a=other, b=1) if isinstance(other, int) else other
        divisor = self.b * o.b
        num, rest = divmod(self.a * o.b, o.a * self.b)
        return Q.from_int(num), Q.reduced(rest, divisor)

    def __eq__(self, value):
        if isinstance(value, Q):
            return self.a == value.a and self.b == value.b
        if isinstance(value, int):
            return self.b == 1 and value == self.a
        return super().__eq__(self, value)