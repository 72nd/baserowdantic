import enum
import random
from typing import Optional

from typing_extensions import Self


class Color(str, enum.Enum):
    """The colors defined and provided by Baserow."""

    DARK_BLUE = "dark-blue"
    """Hex: #acc8f8"""
    DARK_GREEN = "dark-green"
    """Hex: #a0eeba"""
    DARK_CYAN = "dark-cyan"
    """Hex: #70e0ef"""
    DARK_YELLOW = "dark-yellow"
    """Hex: #ffdd8f"""
    DARK_ORANGE = "dark-orange"
    """Hex: #ffe9b4"""
    DARK_RED = "dark-red"
    """Hex: #ffbdb4"""
    DARK_BROWN = "dark-brown"
    """Hex: #f5c098"""
    DARK_PURPLE = "dark-purple"
    """Hex: #cf96f2"""
    DARK_PINK = "dark-pink"
    """Hex: #f285d9"""
    DARK_GRAY = "dark-gray"
    """Hex: #b5b5b7"""
    LIGHT_BLUE = "light-blue"
    """Hex: #f0f4fc"""
    LIGHT_GREEN = "light-green"
    """Hex: #ecfcf1"""
    LIGHT_CYAN = "light-cyan"
    """Hex: #cff5fa"""
    LIGHT_YELLOW = "light-yellow"
    """Hex: #fffbf0"""
    LIGHT_ORANGE = "light-orange"
    """Hex: #fffbf0"""
    LIGHT_RED = "light-red"
    """Hex: #fff2f0"""
    LIGHT_BROWN = "light-brown"
    """Hex: #f5e6dc"""
    LIGHT_PURPLE = "light-purple"
    """Hex: #f9f1fd"""
    LIGHT_PINK = "light-pink"
    """Hex: #f7e1f2"""
    LIGHT_GRAY = "light-gray"
    """Hex: #f5f5f5"""
    BLUE = "blue"
    """Hex: #dae4fd"""
    GREEN = "green"
    """Hex: #d0f6dc"""
    CYAN = "cyan"
    """Hex: #a0ebf5"""
    YELLOW = "yellow"
    """Hex: #ffe9b4"""
    ORANGE = "orange"
    """Hex: #fff4da"""
    RED = "red"
    """Hex: #ffdeda"""
    BROWN = "brown"
    """Hex: #f5ceb0"""
    PURPLE = "purple"
    """Hex: #dfb9f7"""
    PINK = "pink"
    """Hex: #f7b2e7"""
    GRAY = "gray"
    """Hex: #d7d8d9"""
    DARKER_BLUE = "darker-blue"
    """Hex: #689ef1"""
    DARKER_GREEN = "darker-green"
    """Hex: #41dd75"""
    DARKER_CYAN = "darker-cyan"
    """Hex: #41d6ea"""
    DARKER_YELLOW = "darker-yellow"
    """Hex: #ffd269"""
    DARKER_ORANGE = "darker-orange"
    """Hex: #ffd269"""
    DARKER_RED = "darker-red"
    """Hex: #ff7b69"""
    DARKER_BROWN = "darker-brown"
    """Hex: #f5a96e"""
    DARKER_PURPLE = "darker-purple"
    """Hex: #bf73ee"""
    DARKER_PINK = "darker-pink"
    """Hex: #ff6dde"""
    DARKER_GRAY = "darker-gray"
    """Hex: #b5b5b7"""

    @classmethod
    def random(cls):
        """
        Returns a random color.
        """
        return random.choice(list(cls))


class BasicColor(str, enum.Enum):
    """
    Limited color palette from Baserow, as used in the rating field, for
    example.
    """

    DARK_BLUE = "dark-blue"
    """Hex: #acc8f8"""
    DARK_GREEN = "dark-green"
    """Hex: #a0eeba"""
    DARK_YELLOW = "dark-yellow"
    """Hex: #ffdd8f"""
    DARK_RED = "dark-red"
    """Hex: #ffbdb4"""

    @classmethod
    def random(cls) -> Self:
        """
        Returns a random color.
        """
        return random.choice(list(cls))


class ColorSequence:
    """
    This class provides the ability to obtain appealing color gradients. Using
    the method `ColorProvider.get_color()`, you can retrieve the colors
    sequentially.
    """

    def __init__(self):
        self.__current_index: int = 0

    def get_color(self) -> Color:
        """
        Returns the next `Color` in the order of the Enum.
        """
        color_list = list(Color)
        rsl = color_list[self.__current_index]
        self.__current_index = (self.__current_index + 1) % len(color_list)
        return rsl
