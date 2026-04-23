from __future__ import annotations

from .base import Framework, FrameworkInput, FrameworkOutput
from .four_p import FourPFramework
from .persona import PersonaFramework
from .stp import STPFramework
from .swot import SWOTFramework
from .three_c import ThreeCFramework

ALL_FRAMEWORKS: list[type[Framework]] = [
    ThreeCFramework,
    STPFramework,
    FourPFramework,
    SWOTFramework,
    PersonaFramework,
]


def get_framework(name: str) -> type[Framework]:
    for cls in ALL_FRAMEWORKS:
        if cls.name == name:
            return cls
    raise KeyError(f"unknown framework: {name}")


__all__ = [
    "ALL_FRAMEWORKS",
    "Framework",
    "FrameworkInput",
    "FrameworkOutput",
    "get_framework",
]
