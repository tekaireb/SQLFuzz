# Defines the grammar type
from typing import Dict, Union, Any, Tuple, List

Option = Dict[str, Any]
Expansion = Union[str, Tuple[str, Option]]
Grammar = Dict[str, List[Expansion]]