
from dataclasses import dataclass
from math import prod
from typing import Any, ClassVar, Self

from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass as PydanticMetaclass

from pairing_bijections import (
    f_to_flist,
    fi_to_i,
    i_to_fi,
    flist_to_f,
    ilist_to_i,
    ii_to_i,
    i_to_ii,
    i_to_ilist
    )

INFINITE_SIZE = -1

class BijStructure(BaseModel):
    size: ClassVar[int] = ...

    def model_post_init(self, context):
        if self.__class__.size == ...:
            raise AttributeError(
                "Classes that directly inherit from BijStructure "
                f"(like {self.__class__.__name__!r}) "
                "must define class attribute 'size: int'")
        return super().model_post_init(context)

    @classmethod
    def decode(cls, code: int) -> Self:
        ...
    
    def encode(self) -> int:
        ...
    
    def validate(self) -> bool:
        ...

def is_valid_class(cls: type) -> bool:
    if not issubclass(cls, BijStructure):
        return False
    if cls.size == ...:
        # class not correctly initialized
        return False
    return True

def assert_valid_class(cls: type, attr_name: str, for_cls: type):
    if not issubclass(cls, BijStructure):
        raise TypeError(
            f"Can only generate a bijection for class {for_cls.__name__!r} "
            "if all attributes inherit from BijStructure!\n"
            f"Attribute '{attr_name}: {cls.__name__}' does not!")
    if cls.size == ...:
        raise AttributeError(
            "Classes directly inheriting from BijStructure (not derived or with generated bijection) "
            "must define class attribute 'size: int'.\n"
            f"Class {cls.__name__!r} does not!"
        )

def _process_add_bijection(cls, exclude: list[str]) -> type[BijStructure]:
    assert issubclass(cls, BijStructure)

    newcls = cls

    include_attrs = [
        (name, info.annotation)
        for name, info
        in cls.model_fields.items()
        if name not in exclude
        ]

    for attr_name, attr_type in include_attrs:
        assert_valid_class(attr_type, attr_name, cls)
    assert len(include_attrs)

    fin_attrs = [
        (name, attr_type)
        for name, attr_type in include_attrs
        if attr_type.size != INFINITE_SIZE
    ]
    fin_maxes = [
        attr_type.size
        for _, attr_type
        in fin_attrs
    ]
    inf_attrs = [
        (name, attr_type)
        for name, attr_type in include_attrs
        if attr_type.size == INFINITE_SIZE
    ]

    finmax = prod(attr_type.size for _, attr_type in fin_attrs)
    finnum = len(fin_attrs)
    infnum = len(inf_attrs)

    newcls.size = INFINITE_SIZE if inf_attrs else finmax

    def decode(cls, code: int):
        """does not allow for excluded attributes yet!"""
        fin_code, inf_code = i_to_fi(code, m=finmax)
        fin_attr_codes = f_to_flist(fin_code, length=finnum, maxes=fin_maxes)
        inf_attr_codes = i_to_ilist(inf_code, length=infnum)
        fin_self_attrs = {
            attr_name: attr_cls.decode(f_code)
            for (attr_name, attr_cls), f_code
            in zip(fin_attrs, fin_attr_codes)}
        inf_self_attrs = {
            attr_name: attr_cls.decode(i_code)
            for (attr_name, attr_cls), i_code
            in zip(inf_attrs, inf_attr_codes)}
        return cls(**fin_self_attrs, **inf_self_attrs)

    def encode(self: BijStructure) -> int:
        fin_attr_codes = [
            self.__getattribute__(attr_name).encode()
            for attr_name, _ in fin_attrs]
        inf_attr_codes = [
            self.__getattribute__(attr_name).encode()
            for attr_name, _ in inf_attrs]
        
        fin_code = flist_to_f(fin_attr_codes, maxes=fin_maxes)
        inf_code = ilist_to_i(inf_attr_codes)
        return fi_to_i(fin_code, inf_code, m=finmax)

    newcls.decode = classmethod(decode)
    newcls.encode = encode
    
    return cls

def generate_bijection(
        cls: type[BijStructure] = None, /, *,
        exclude: list[str] = []
        ) -> type[BijStructure]:
    
    def wrapper(cls):
        return _process_add_bijection(cls, exclude=exclude)

    # Determining if called with () or without
    if cls is None:
        # With ()
        return wrapper

    return wrapper(cls)

def class_has_method(cls, method_name: str, method_type: type = None) -> bool:
    """method_type can be staticmethod or classmethod"""
    method = cls.__dict__.get(method_name, None)
    return callable(method) if method_type is None else isinstance(method, method_type)

def _process_derive(cls, aux_class: type[BijStructure]) -> type[BijStructure]:
    assert issubclass(cls, BijStructure)
    assert issubclass(aux_class, BijStructure)

    if not class_has_method(cls, "to_aux"):
        raise AttributeError(
            "classes that derive another class should implement a 'to_aux' method! "
            f"{cls.__name__!r} does not!")
    if not class_has_method(cls, "from_aux", classmethod):
        raise AttributeError(
            "classes that derive another class should implement a 'from_aux' classmethod! "
            f"{cls.__name__!r} does not!")
    
    def decode(cls, code: int) -> Self:
        aux_obj = aux_class.decode(code)
        return cls.from_aux(aux_obj)
    def encode(self):
        aux_obj: BijStructure = self.to_aux()
        if not isinstance(aux_obj, aux_class):
            raise ValueError(
                "The method 'to_aux' of classes deriving another BijStructure class <C> "
                "must return an object of type <C> (or whatever the name)\n"
                f"to_aux({repr(self)}) returned `{repr(aux_obj)}` of class"
                f" {aux_obj.__class__.__name__!r}, "
                f"not {aux_class.__name__!r} (the derived class)!")
        return aux_obj.encode()
    
    newcls = cls
    newcls.size = aux_class.size
    newcls.decode = classmethod(decode)
    newcls.encode = encode
    
    return newcls

def derive(
        cls: type = None, /, *,
        aux_class: type[BijStructure]
        )  -> type[BijStructure]:
    
    def wrapper(cls):
        return _process_derive(cls, aux_class)
    
    if cls is None:
        return wrapper

    return wrapper(cls)


class N0(BijStructure):
    size: ClassVar[int] = INFINITE_SIZE
    n: int
    @classmethod
    def decode(cls, code):
        return cls(n=code)
    def encode(self):
        return self.n
    
@derive(aux_class=N0)
class N1(BijStructure):
    n: int

    def to_aux(self):
        return N0(n=self.n-1)
    @classmethod
    def from_aux(cls, aux_obj):
        return cls(n = aux_obj.n+1)

@derive(aux_class=N0)
class Z(BijStructure):
    z: int

    def to_aux(self):
        bonus = self.z < 0
        return N0(n=2*abs(self.z) + bonus)
    @classmethod
    def from_aux(cls, aux_obj):
        neg = aux_obj.n % 2
        z = (-1 if neg else 1) * (aux_obj.n - neg) // 2
        return cls(z=z)

@generate_bijection
class IntPair(BijStructure):
    a: Z
    b: Z


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


obj = N0(n=123)
print(z:=obj.encode())
print(N0.decode(z))
print("---")

obj = Z(z=-123)
print(z:=obj.encode())
print(Z.decode(z))
print("---")

obj = IntPair(a=Z(z=12), b=Z(z=43))
print(z:=obj.encode())
print(IntPair.decode(z))
print("---")