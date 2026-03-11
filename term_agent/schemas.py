from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ManualSuggestion:
    command: str
    description: str


@dataclass(frozen=True)
class ManualResult:
    suggestions: List[ManualSuggestion]
