
from typing import Any, ClassVar
from hashlib import sha256 as static_hash

from bij_type import INFINITE_SIZE, BijType
from decorators import assert_in_cls_range, bijectable_version
from helpers import classcopy, first_index_where, scan
from pairing_bijections import fi_to_i, i_to_fi  

# @generate_bijection(exclude=["alphabet"])
class AlphabetString(BijType):
    """assumes the given alphabet and does not encode it."""
    alphabet: str
    string: str

class UnionType(BijType):
    _types: ClassVar[tuple[type]] = ...

    def __instancecheck__(self, instance) -> bool:
        return any((
            isinstance(instance, cls)
            for cls in self._types
        ))
    
    @classmethod
    def _isinstance_exact(cls, instance) -> bool:
        return type(instance) in cls._types

def assert_isinstance_exact(cls: UnionType, instance):
    if cls._isinstance_exact(instance):
        return
    raise TypeError(f"Instance for `union(...).encode` has to "
                    f"be instance of any of {cls._types} (not subclass)!")

def union(*types: BijType) -> type[BijType]:
    """Union of types: Encode any object of the given types.\n
    Two Union types are the same if the set of their types is the same.\n
    `union(types).encode()` does not allow for inputs that are a subclass of `types`."""
    # the union is the same if reordered or a type appears multiple times
    types = sorted(set(types), key=lambda cls: cls.__name__)
    types = tuple(types)

    bij_version = {cls: bijectable_version(cls) for cls in types}

    fin_types = [cls for cls in types if bij_version[cls].size != INFINITE_SIZE]
    fin_starts = list(scan(
        lambda a,b: a+b ,
        (cls.size for cls in fin_types),
        acc=0,
        yield_start=True
    ))
    inf_types = [cls for cls in types if bij_version[cls].size == INFINITE_SIZE]
    
    fin_sum = fin_starts[-1]
    inf_num = len(inf_types)

    classstr = "".join(cls.__name__ for cls in types)
    typehash = static_hash(classstr.encode())
    typestr = typehash.hexdigest()[2:10]

    newcls = classcopy(UnionType, f"Union_{typestr}")
    newcls._types = types

    def encode_fin(self: BijType) -> int:
        fin_index = fin_types.index(type(self))
        bij_cls_version = bij_version[type(self)]

        code_in_cls = bij_cls_version.encode(self)
        base = fin_starts[fin_index]
        return base + code_in_cls
    
    def encode_inf(self: BijType) -> int:
        inf_index = inf_types.index(type(self))
        bij_cls_version = bij_version[type(self)]

        code_in_cls = bij_cls_version.encode(self)
        return fin_sum + fi_to_i(inf_index, code_in_cls, m=inf_num)
    
    def encode(self) -> int:
        assert_isinstance_exact(newcls, self)
        return encode_fin(self) if self.__class__ in fin_types else encode_inf(self)

    def decode_fin(code: int) -> Any:
        fin_index_plus1 = first_index_where(lambda el: code < el, fin_starts)
        assert fin_index_plus1 is not None
        base = fin_starts[fin_index_plus1-1]
        code_in_cls = code - base

        cls = fin_types[fin_index_plus1-1]
        bij_cls_version = bij_version[cls]
        return bij_cls_version.decode(code_in_cls)
    
    def decode_inf(code: int) -> Any:
        inf_index, code_in_type = i_to_fi(code, m=inf_num)
        cls = inf_types[inf_index]
        bij_cls_version = bij_version[cls]
        return bij_cls_version.decode(code_in_type)
    
    def decode(cls, code: int) -> Any:
        assert_in_cls_range(cls, code)
        return decode_fin(code) if code < fin_sum else decode_inf(code-fin_sum)
    
    newcls.size = INFINITE_SIZE if inf_types else fin_sum
    newcls.encode = encode
    newcls.decode = classmethod(decode)
    return newcls

