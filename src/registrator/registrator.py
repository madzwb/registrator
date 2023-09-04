
from __future__ import annotations

import inspect
import sys

from collections import UserDict
from typing import Any, Callable, cast#, Type


"""Return dict of classes by restrictions."""
def register(
        name    : str           = "",
        module  : str           = __name__,
        env     : dict[Any, Any]= globals(),
        base    : type|None     = None,
        filters : list[str]     = ["__builtins__"],
        replace : bool          = True,
    ) -> dict[str, Callable]\
    :
    result = {}
    if base is None:
        base = object
    attributes = dir(sys.modules[module])
    for attribute in attributes:
        if attribute not in env:
            continue

        if attribute in filters:
            continue

        if not name or name in attribute:

            _type = env[attribute]

            if  check(_type, base, False):
                if replace:
                    key = attribute.replace(name,"")
                else:
                    key = attribute
                if key:
                    result[key.lower()] = _type
    return result

def check(_type: type|Callable, _base: type, throw = False) -> bool: # type: ignore
    if      _type is not None                               \
        and callable(_type)                                 \
        and (                                               \
                (                                           \
                            inspect.isclass(_type)          \
                    and     _type != _base                  \
                    and     issubclass(_type, _base)        \
                    and not inspect.isabstract(_type)       \
                )                                           \
                or                                          \
                (                                           \
                            inspect.isfunction(_type)       \
                    and     type(_type) == _base            \
                    and     issubclass(type(_type), _base)  \
                )                                           \
            )                                               \
    :
        return True
    elif throw:
        if not callable(_type):
            raise TypeError(f"Type:'{_type}' is not callable.")
        elif inspect.isabstract(_type):
            raise TypeError(f"Type:'{_type}' is abstract class.")
        elif not issubclass(cast(type, _type), _base):
            info = f"Type:'{_type}' is not a subclass of '"
            info += f"{_base.__name__}" if hasattr(_base,"__name__") else f"{_base}"
            info += "'."
            raise TypeError(info)
    else:
        return False



class REGISTRATOR(UserDict):

    attribute   : str               = "alias"
    _instance   : REGISTRATOR|None  = None
    _initialized: bool              = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance       = super().__new__(cls, *args, **kwargs)
            cls._initialized    = False
        return cls._instance

    def __init__(self, *args, **kwargs):
        if self._initialized:
            return
        self._initialized = True
        super().__init__(*args, **kwargs)
    
    @classmethod
    def register(
            cls,
            name    : str           = "",
            module  : str           = __name__,
            env     : dict[Any, Any]= globals(),
            base    : type|None     = None,
            filters : list[str]     = ["__builtins__"],
            replace : bool          = False,
        ):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        if cls._instance is not None and not cls._initialized:
            cls._instance.__init__()
        if base is not None:
            cls._base = base

        data = register(name, module, env, base, filters, replace)
        for key, value in data.items():
            setattr(value, cls.attribute, key)
        cls._instance.update(data)

    @classmethod
    def check(cls, _type: type|Callable, throw: bool = False) -> bool:
        return check(_type, cls._base, throw)

    def __call__(self, *args: Any, **kwargs: Any) -> dict|object:
        if args and args[0]:
            key = args[0]
            return self[key]
        else:
            return REGISTRATOR._instance

    def __getitem__(self, key:  str):
        return super().__getitem__(key)
    
    def __setitem__(self, key: str, cls: type|Callable|None = None):
        if cls is None:
            if super().__contains__(key):
                super().__delitem__(key)
            else:
                raise KeyError(f"In dict:'{super(UserDict,self).__repr__()}', key:'{key}' not found.")
        elif self.check(cls, True):
            setattr(cls, self.attribute, key)
            super().__setitem__(key,cls)
