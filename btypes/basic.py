
from typing import ClassVar

from bij_type import INFINITE_SIZE, BijType
from decorators import derive, generate_bijection
from helpers import classcopy, first_index_where, first_where, scan
from pairing_bijections import fi_to_i, i_to_fi  

# @generate_bijection(exclude=["alphabet"])
class AlphabetString(BijType):
    """assumes the given alphabet and does not encode it."""
    alphabet: str
    string: str
