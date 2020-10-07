from .mapper000 import Mapper000
from .mapper002 import Mapper002
from .mapper004 import Mapper004
from .mapper064 import Mapper064
from .mapper066 import Mapper066

MAPPERS = {
    0: Mapper000,
    2: Mapper002,
    4: Mapper004,
    64: Mapper064,
    66: Mapper066
}

__all__ = ['MAPPERS', 'Mapper000', 'Mapper002', 'Mapper004', 'Mapper064', 'Mapper066']
