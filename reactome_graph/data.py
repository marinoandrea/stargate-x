from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class Pathway:
    id: str
    name: str
    is_top_level: bool
    in_disease: bool


@dataclass(frozen=True, eq=True)
class Compartment:
    id: str
    name: str
