from typing import Any, Callable

from pydantic import BaseModel


class Bijection(BaseModel):
    pro:    Callable[[Any], Any] # Function
    retro:  Callable[[Any], Any] # Inverse Function
    static_argnames: list[str]

class BijConfig(BaseModel):
    ff_f: Bijection
    fi_i: Bijection
    ii_i: Bijection
    flist_f: Bijection
    ilist_i: Bijection
    iset_ilist: Bijection