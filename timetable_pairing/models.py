from dataclasses import dataclass
from typing import List


@dataclass
class Teacher:
    name: str
    slots: List[int]
    hours: int
