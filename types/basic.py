
from typing import ClassVar

from bij_types import INFINITE_SIZE, BijType
from decorators import derive, generate_bijection  

# @generate_bijection(exclude=["alphabet"])
class AlphabetString(BijType):
    """assumes the given alphabet and does not encode it."""
    alphabet: str
    string: str
