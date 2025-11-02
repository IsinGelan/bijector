
from enum import Enum
from math import prod
from typing import Callable, ClassVar, Self
import inspect

from pydantic import BaseModel

from bij_type import BijAdapter, BijType, INFINITE_SIZE
from helpers import classcopy
from pairing_bijections import (
    f_to_flist,
    fi_to_i,
    i_to_fi,
    flist_to_f,
    ilist_to_i,
    i_to_ilist
    )

# ================================
PRIMITIVE_ADAPTERS: dict[type, type[BijType]] = {}
SUPPORTED_BASE_CLASSES = {BijType, Enum}

def is_bijectable_type(cls: type) -> bool:
    """whether the type itself is bijectable"""
    if issubclass(cls, BijType):
        return cls.size != ...
    
    attrs = dir(cls)
    if "encode" not in attrs or not inspect.ismethod(getattr(cls, "encode")):
        return False
    if "decode" not in attrs or not inspect.ismethod(getattr(cls, "decode")):
        return False
    if "size" not in attrs:
        return False
    return True

def has_bijectable_version(cls: type) -> bool:
    """whether the type can be converted to a bijectable version"""
    return (
        is_bijectable_type(cls)
        or cls in PRIMITIVE_ADAPTERS
        )

def bijectable_version(cls: type) -> type[BijType]:
    """returns the bijectable version of that class.
    If class is not subclass of BijStructure, but an adapter for the class exists, it is returned (e.g. for int)"""
    if is_bijectable_type(cls):
        return cls
    if cls in PRIMITIVE_ADAPTERS:
        return PRIMITIVE_ADAPTERS[cls]
    raise TypeError(f"Class {cls.__name__!r} is not bijectable and does not define an adapter!")

# --------------------------------
def assert_aux_obj_type(aux_obj, aux_cls):
    if isinstance(aux_obj, aux_cls):
        return
    if issubclass(aux_cls, BijAdapter):
        # Object doesn't haev to be instance of the class that constructed it
        # because it was constructed by an adapter
        return
    aux_cls_repr = f"{aux_cls.__name__!r}"
    obj_cls_repr = f"{aux_obj.__class__.__name__!r}"
    raise ValueError(
        f"The method 'to_aux' of classes deriving another BijStructure class {aux_cls_repr} "
        f"must return an object of type {aux_cls_repr}\n"
        f"to_aux(...) returned `{repr(aux_obj)}` of class"
        f" {obj_cls_repr}, not {aux_cls_repr} (the derived class)!")

def assert_in_cls_range(cls, code: int):
    if cls.size == INFINITE_SIZE:
        return
    if cls.size == ...:
        raise AttributeError(
            "Classes directly inheriting from BijType (not derived or with generated bijection) "
            "must define class attribute 'size: int'.\n"
            f"Class {cls.__name__!r} does not!"
        )
    if code < cls.size:
        return
    raise IndexError(f"Code {code} beyond finite size of {cls.size} "
                     f"for class {cls.__name__!r}!")

def assert_bijectable_class(cls: type, attr_name: str, for_cls: type):
    if cls in PRIMITIVE_ADAPTERS:
        return
    if not is_bijectable_type(cls):
        raise TypeError(
            f"Can only generate a bijection for class {for_cls.__name__!r} "
            "if all attributes are bijectable or have an adapter!\n"
            f"Attribute '{attr_name}: {cls.__name__}' does not!")
    if cls.size == ...:
        raise AttributeError(
            "Classes directly inheriting from BijType (not derived or with generated bijection) "
            "must define class attribute 'size: int'.\n"
            f"Class {cls.__name__!r} does not!"
        )

# --------------------------------
def new_adapter(cls, aux_cls) -> type[BijAdapter]:
    return classcopy(BijAdapter, f"Adapter{cls.__name__}{aux_cls.__name__}")

def _process_derive[CT, AuxT](
        cls: CT,
        aux_cls: AuxT,
        to_aux: Callable[[CT], AuxT],
        from_aux: Callable[[AuxT], CT],
        as_decorator: bool
        ) -> type[BijType]:
    
    assert has_bijectable_version(aux_cls)
    assert not as_decorator or issubclass(cls, BaseModel) # TODO: extend to other bijectable types

    bij_aux_cls = bijectable_version(aux_cls)
    
    def decode(code: int) -> Self:
        assert_in_cls_range(newcls, code)
        aux_obj = bij_aux_cls.decode(code)
        return from_aux(aux_obj)
    
    def encode(self):
        aux_obj = to_aux(self)
        assert_aux_obj_type(aux_obj, bij_aux_cls)
        return bij_aux_cls.encode(aux_obj)
    
    newcls = cls if as_decorator else new_adapter(cls, aux_cls)
    newcls.size = bij_aux_cls.size
    newcls.__cls = cls
    newcls.__aux_cls = bij_aux_cls
    newcls.__desc = f"Adapter({cls.__name__} ~> {bij_aux_cls.__name__})"
    # decode is static, not a classmethod as this allows to return objects
    # that are not of the type of newcls (the returned class);
    # helpful for using newcls as an adapter to primitive types
    newcls.decode = staticmethod(decode)
    newcls.encode = encode
    
    return newcls

def derive[CT, AuxT](
        cls1,
        cls2 = None, /, *,
        to_aux: Callable[[CT], AuxT],
        from_aux: Callable[[AuxT], CT]
        ) -> type[BijType]:
    """To derive a class from an auxiliary type"""

    aux_cls = cls1 if cls2 is None else cls2

    def wrapper(cls):
        return _process_derive(cls, aux_cls, to_aux=to_aux, from_aux=from_aux, as_decorator=cls2 is None)
    
    if cls2 is None:
        return wrapper

    return wrapper(cls1)



def _process_gb_enum(cls: type[Enum]) -> type:
    values = list(cls)
    values_to_index = {v: i for i, v in enumerate(values)}
    value_num = len(values)

    def decode(cls, code: int) -> Self:
        assert_in_cls_range(cls, code)
        return values[code]

    def encode(self) -> int:
        return values_to_index[self]

    cls.size = value_num
    cls.decode = classmethod(decode)
    cls.encode = encode

    return cls

def replace_adapter_types(cls: type[BijType], attr_names: list[str]):
    """Inplace"""
    for attr_name in attr_names:
        attr_type = cls.model_fields[attr_name].annotation
        if attr_type in PRIMITIVE_ADAPTERS:
            cls.model_fields[attr_name].annotation = PRIMITIVE_ADAPTERS[attr_type]

def _process_gb_pydantic(cls, exclude: list[str]) -> type[BijType]:
    assert issubclass(cls, BaseModel)

    include_attr_names = [
        attr_name
        for attr_name
        in cls.model_fields
        if attr_name not in exclude
        ]
    
    replace_adapter_types(cls, include_attr_names)

    # Must come after the primitives were replaced by adapters!
    include_attr_types: list[type[BijType]] = [
        cls.model_fields[attr_name].annotation
        for attr_name in include_attr_names
    ]
    
    for attr_name in include_attr_names:
        attr_type = cls.model_fields[attr_name].annotation
        assert_bijectable_class(attr_type, attr_name, cls)

    fin_attrs = [
        (name, attr_type)
        for name, attr_type in zip(include_attr_names, include_attr_types)
        if attr_type.size != INFINITE_SIZE
    ]
    fin_maxes = [
        attr_type.size
        for _, attr_type
        in fin_attrs
    ]
    inf_attrs = [
        (name, attr_type)
        for name, attr_type in zip(include_attr_names, include_attr_types)
        if attr_type.size == INFINITE_SIZE
    ]

    finmax = prod(attr_type.size for _, attr_type in fin_attrs)
    finnum = len(fin_attrs)
    infnum = len(inf_attrs)
 
    def decode(cls, code: int):
        """does not allow for excluded attributes yet!"""
        assert_in_cls_range(cls, code)
        fin_code, inf_code = i_to_fi(code, m=finmax)
        fin_attr_codes = f_to_flist(fin_code, length=finnum, maxes=fin_maxes)
        inf_attr_codes = i_to_ilist(inf_code, length=infnum)
        fin_self_attrs = {
            attr_name: attr_type.decode(f_code)
            for (attr_name, attr_type), f_code
            in zip(fin_attrs, fin_attr_codes)}
        inf_self_attrs = {
            attr_name: attr_type.decode(i_code)
            for (attr_name, attr_type), i_code
            in zip(inf_attrs, inf_attr_codes)}
        return cls(**fin_self_attrs, **inf_self_attrs)

    def encode(self: BijType) -> int:
        fin_attr_codes = [
            attr_type.encode(self.__getattribute__(attr_name)) # current workaround for adapters
            for attr_name, attr_type in fin_attrs]
        inf_attr_codes = [
            attr_type.encode(self.__getattribute__(attr_name))
            for attr_name, attr_type in inf_attrs]
    
        
        fin_code = flist_to_f(fin_attr_codes, maxes=fin_maxes)
        inf_code = ilist_to_i(inf_attr_codes)
        return fi_to_i(fin_code, inf_code, m=finmax)

    cls.size = INFINITE_SIZE if inf_attrs else finmax
    cls.decode = classmethod(decode)
    cls.encode = encode
    
    return cls

def _process_gb(cls: type, exclude: list[str] = []):
    """processes the class; if class type not supported, raise Exception"""
    if issubclass(cls, Enum):
        return _process_gb_enum(cls)
    if issubclass(cls, BaseModel):
        return _process_gb_pydantic(cls, exclude=exclude)
    raise TypeError(
        f"@generate_bijection does not support class {cls.__name__!r}!\n"
        f"Only classes inheriting from any of {SUPPORTED_BASE_CLASSES!r} are supported."
        )

def generate_bijection(
        cls: type[BijType] = None, /, *,
        exclude: list[str] = []
        ) -> type[BijType]:
    """Atomatically adds methods encode and decode to the class to make it bijectable."""
    
    def wrapper(cls):
        return _process_gb(cls)

    # Determining if called with () or without
    if cls is None:
        # With ()
        return wrapper

    return wrapper(cls)



# ================================
# Configuring the adapters
class N0(BijType):
    size: ClassVar[int] = INFINITE_SIZE
    n: int
    @classmethod
    def decode(cls, code):
        return cls(n=code)
    def encode(self):
        return self.n

z_to_n0 = lambda z: N0(n=2*abs(z.z) + (z.z < 0))
z_from_n0 = lambda n0: Z(z=(-1 if (neg := n0.n % 2) else 1) * (n0.n - neg) // 2)

@derive(N0, to_aux=z_to_n0, from_aux=z_from_n0)
class Z(BijType):
    z: int

class Boolean(Enum):
    FALSE = 0
    TRUE  = 1

b_to_bij = lambda b: Boolean.TRUE if b else Boolean.FALSE
bij_to_b = lambda bij: bij == Boolean.TRUE


PRIMITIVE_ADAPTERS = {
    int: derive(int, Z, to_aux=lambda i: Z(z=i), from_aux=lambda z: z.z),
    bool: derive(bool, Boolean, to_aux=b_to_bij, from_aux=bij_to_b)
}