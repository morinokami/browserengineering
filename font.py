import tkinter.font
from typing import Literal

FONTS = {}


def get_font(
    size: int, weight: Literal["normal", "bold"], slant: Literal["roman", "italic"]
) -> tkinter.font.Font:
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]
