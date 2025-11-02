
from typing import ClassVar, Self
from pydantic import BaseModel

INFINITE_SIZE = -1

class BijType(BaseModel):
    size: ClassVar[int] = ...

    def model_post_init(self, context):
        if self.__class__.size == ...:
            raise AttributeError(
                "Classes that directly inherit from BijStructure "
                f"(like {self.__class__.__name__!r}) "
                "must define class attribute 'size: int'")
        
        self.validate()

        return super().model_post_init(context)

    @classmethod
    def decode(cls, code: int) -> Self:
        ...
    
    def encode(self) -> int:
        ...
    
    def validate(self) -> bool:
        ...

class BijAdapter(BijType):
    """Class for adapters that make primitive data types encodable"""
    __cls: ClassVar[type]
    __aux_cls: ClassVar[type]