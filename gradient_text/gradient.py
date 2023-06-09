"""Defines the Gradient class which is used to print text with a gradient.\
    It inherits from the Rich Text class."""
# pylint: disable=E0401, R0902, C0103, E0202, W1514
import re
from pathlib import Path
from typing import List, Optional, Tuple

from cheap_repr import normal_repr, register_repr
from lorem_text import lorem
from numpy import arange, array_split, ndarray
from rich.color import ColorParseError
from rich.console import Console, JustifyMethod, OverflowMethod
from rich.control import strip_control_codes
from rich.panel import Panel
from rich.pretty import Pretty
from rich.style import Style, StyleType
from rich.table import Table
from rich.text import Span, Text

from gradient_text.color import Color
from gradient_text.color_list import ColorList

# from gradient_text._gradient_substring import GradientSubstring
from gradient_text.log import get_console, log
from gradient_text.theme import GradientTheme

# from pygments.lexers.python import CythonLexer
# from snoop import snoop


# from loguru import logger


DEFAULT_JUSTIFY: "JustifyMethod" = "default"
DEFAULT_OVERFLOW: "OverflowMethod" = "fold"
WHITESPACE_REGEX = re.compile(r"^\s+$")
VERBOSE: bool = True
CWD = Path.cwd()
EXAMPLE_DIR = CWD / "examples"

console = get_console()

register_repr(Pretty)(normal_repr)
register_repr(Text)(normal_repr)
register_repr(Table)(normal_repr)
register_repr(Color)(normal_repr)
register_repr(ColorList)(normal_repr)


class Gradient(Text):
    """Text with gradient color / style.

        Args:
            text(`text): The text to print. Defaults to `""`.\n
            colors(`List[Optional[Color|Tuple|str|int]]`): A list of colors to use \
                for the gradient. Defaults to None.\n
            rainbow(`bool`): Whether to print the gradient text in rainbow colors across \
                the spectrum. Defaults to False.\n
            invert(`bool`): Reverse the color gradient. Defaults to False.\n
            hues(`int`): The number of colors in the gradient. Defaults to `3`.\n
            color_sample(`bool`): Replace text with characters with `"█" `. Defaults to False.\n
            style(`StyleType`) The style of the gradient text. Defaults to None.\n
            justify(`Optional[JustifyMethod]`): Justify method: "left", "center", "full", \
                "right". Defaults to None.\n
            overflow(`Optional[OverflowMethod]`):  Overflow method: "crop", "fold", \
                "ellipsis". Defaults to None.\n
            end (str, optional): Character to end text with. Defaults to "\\\\n".\n
            no_wrap (bool, optional): Disable text wrapping, or None for default.\
                Defaults to None.\n
            tab_size (int): Number of spaces per tab, or `None` to use `console.tab_size`.\
                Defaults to 8.\n
            spans (List[Span], optional). A list of predefined style spans. Defaults to None.\n

    """

    __slots__ = [
        "invert",
        "_rainbow",
        "hues",
        "_colors",
        "_color_sample",
        "_style",
        "verbose",
    ]

    # @snoop(watch=("gradient_spans", "substrings"))
    def __init__(
        self,
        text: Optional[str | Text] = "",
        colors: Optional[List[Color | Tuple | str]] = None,
        rainbow: bool = False,
        invert: bool = False,
        hues: int = 3,
        color_sample: bool = False,
        style: StyleType = Style.null(),
        *,
        justify: Optional[JustifyMethod] = None,
        overflow: Optional[OverflowMethod] = None,
        no_wrap: Optional[bool] = None,
        end: str = "\n",
        tab_size: Optional[int] = 8,
        spans: Optional[List[Span]] = None,
    ) -> None:
        """Generate a gradient text object."""
        if colors is None:
            self._colors: List[Color] = []
        if spans is None:
            spans: List[Span] = []
        if isinstance(text, Text):
            text = text.plain
            spans = text.spans

        super().__init__(
            text=text,
            style=style,
            justify=justify,
            overflow=overflow,
            no_wrap=no_wrap,
            end=end,
            tab_size=tab_size,
            spans=spans,
        )
        if color_sample:
            self._text = "█" * self._length

        self.hues = hues
        if rainbow:
            self.hues = 10

        self.style = style

        # Colors
        if colors:
            assert isinstance(colors, List), "Colors must be a list."
            self._colors = []
            for color in colors:
                try:
                    parsed_color = Color(color)
                    self._colors.append(parsed_color)
                except ColorParseError as cpe:
                    raise ColorParseError(f"Unable to parse color: {color}") from cpe
        elif colors is None:
            colors = ColorList(invert=invert).color_list[0 : self.hues]
            for color in colors:
                self._colors.append(Color(color))
        else:
            raise ValueError("Colors must be a list of colors.")

        assert len(self._colors) > 1, "Gradient must have at least two colors."
        assert (
            len(self._colors) < self._length
        ), "Gradient must have fewer colors than characters."

        substring_indexes: List[List[int]] = self._substring_indexes()
        spans = self._substring_spans(substring_indexes)
        self._spans = self.simplify_spans(spans)

    def _substring_indexes(self) -> List[Tuple[int, int]]:
        """Calculate the indexes of the gradient's substrings."""
        log.debug("Generating substring indexes.")
        length = self._length
        gradients = self.hues - 1
        arrays: ndarray = array_split(arange(length), gradients)
        substring_indexes: List[List[int]] = [array.tolist() for array in arrays]
        return substring_indexes

    def _substring_spans(self, indexes: List[List[int]]) -> List[Span]:
        """Generate the gradient's spans."""
        log.debug("Generating gradient spans. Colors:")
        for color in self._colors:
            log.debug(f"Colors: {color}")
        spans: List[Span] = []
        for main_index, substring_index in enumerate(indexes):
            substring_length = len(substring_index)
            log.debug(f"Substring Length: {substring_length}")
            log.debug(f"Main Index: {main_index}")

            if main_index < self.hues:
                color1: Color = self._colors[main_index]
                r1, g1, b1 = color1.rgb_tuple
                color2: Color = self._colors[main_index + 1]
                r2, g2, b2 = color2.rgb_tuple
                dr = r2 - r1
                dg = g2 - g1
                db = b2 - b1

            for index in range(substring_length):
                blend = index / substring_length
                red = f"{int(r1 + dr * blend):02X}"
                green = f"{int(g1 + dg * blend):02X}"
                blue = f"{int(b1 + db * blend):02X}"
                hex_color = f"#{red}{green}{blue}"
                span_style = Style(color=hex_color) + self.style
                span_start = substring_index[index]
                span_end = substring_index[index] + 1
                span = Span(span_start, span_end, span_style)
                spans.append(span)
        return spans

    def simplify_spans(self, spans: List[Span]) -> List[Span]:
        """Simplify the spans by combining abutting spans that have identical styles.

        Args:
            spans (List[Span]): A list of spans.

        Returns:
            List[Span]: A list of simplified spans.Hel
        """
        simplified_spans: List[Span] = []
        for index, span in enumerate(spans):
            if index == 0:
                last_span: Span = span
            else:
                if span.style == last_span.style:
                    start = last_span.start
                    last_span = Span(start, span.end, span.style)
                else:
                    simplified_spans.append(last_span)
                    last_span = span
        simplified_spans.append(last_span)
        return simplified_spans

    @property
    def text(self) -> str:
        """The text of the gradient."""
        log.debug(f"Getting gradient._text: {self._text}")
        return self._text

    @text.setter
    def text(self, text: Optional[str | Text]) -> None:
        """Set the text of the gradient."""
        log.debug(f"Setting gradient._text: {text}")
        if isinstance(text, Text):
            sanitized_text = strip_control_codes(text.plain)
            self._length = len(sanitized_text)
            self._text = [sanitized_text]
            self._spans: List[Span] = text.spans
        if isinstance(text, str):
            if text == "":
                raise ValueError("Text cannot be empty.")
            sanitized_text = strip_control_codes(text)
            self._length = len(sanitized_text)
            self._text = sanitized_text

    @property
    def style(self) -> Style:
        """The style of the gradient."""
        # log.debug("Retrieving gradient._style")
        return self._style

    @style.setter
    def style(self, style: Style) -> None:
        """Set the style of the gradient."""
        log.debug(f"Setting gradient._style: {style}")
        if style is None or style == "null":
            self._style = Style()
        self._style = Style.parse(style)

    @property
    def rainbow(self) -> bool:
        """Whether the gradient is rainbow."""
        # log.debug(f"Retrieving gradient._rainbow: {self.rainbow}")
        return self._rainbow

    @rainbow.setter
    def rainbow(self, rainbow: bool) -> None:
        """Set whether the gradient is rainbow."""
        # log.debug(f"Setting gradient._rainbow: {rainbow}")
        self._rainbow = rainbow

    @property
    def color_sample(self) -> bool:
        """Whether the gradient is a color sample."""
        # log.debug(f"Retrieving gradient._color_sample: {self._color_sample}")
        return self._color_sample

    @color_sample.setter
    def color_sample(self, color_sample: bool) -> None:
        """Set whether the gradient is a color sample."""
        log.debug(f"Setting gradient._color_sample: {color_sample}")
        if color_sample:
            self.text = "█" * self._length
        self._color_sample = color_sample

    @property
    def gradient_size(self) -> int:
        """The size of each gradient substring."""
        length = self._length
        gradients = self.hues - 1
        return length // gradients

    def generate_style(self, color: str) -> Style:
        """Generate a style for a color."""
        new_style = self.style + Style(color=color)
        # log.debug(f"Generating style for `{color}`: {new_style}")
        return new_style

    def _gradient_spans(self) -> List[List[int]]:
        """Generate gradient spans."""
        log.debug("Generating gradient spans.")
        gradient_spans: List[List[int]] = []

        # substrings = self.generate_indexes()

        length = self._length
        gradients = self.hues - 1
        gradient_size = length // gradients
        for i in range(gradients):
            begin = i * gradient_size
            end = begin + gradient_size
            if i == gradients:
                end = length
            _substring = self._text[begin:end]

            log.debug(f"Generating gradient span for `{_substring}`.")

            if i < gradients:
                color1 = self._colors[i]
                r1, g1, b1 = color1.rgb_tuple
                color2 = self._colors[i + 1]
                r2, g2, b2 = color2.rgb_tuple
                dr = r2 - r1
                dg = g2 - g1
                db = b2 - b1

            for j in range(gradient_size):
                blend = j / gradient_size
                red = f"{int(r1 + dr * blend):02X}"
                green = f"{int(g1 + dg * blend):02X}"
                blue = f"{int(b1 + db * blend):02X}"
                color = f"#{red}{green}{blue}"
                style = Style(color=color) + self.style
                full_index = begin + j
                new_span = Span[full_index, full_index + 1, style]
                gradient_spans.append(new_span)

        return gradient_spans

    def generate_indexes(self) -> List[List[int]]:
        """Generate indexes for a gradient."""
        substring_arrays: ndarray = array_split(arange(self._length), self.hues - 1)
        substring_indexes: List[List[int]] = [
            index.tolist() for index in substring_arrays
        ]

        indexes: List[Tuple[int]] = []
        for substring in substring_indexes:
            start = substring[0]
            end = substring[-1]
            indexes.append(tuple(start, end))

    def simple_example(self) -> Panel:
        """Generate and print the code to create a simple gradient\
            as well as the simple gradient."""
        _console = "[white]console.[/]"
        _print = "[#4EF87A]print[/]"
        _left_p = "[white]([/])"


if __name__ == "__main__":
    example_console = Console(theme=GradientTheme(), record=True)

    example_console.line(3)
    text1 = "The quick brown fox jumps over the lazy dog."
    gradient1 = Gradient(text1, colors=["red", "magenta", "violet"], style="bold")
    panel1 = Panel(
        gradient1,
        title="[b u white]Simple Gradient[/]",
        padding=(1, 4),
        subtitle="[white]colors = [[/] [bold #ff0000]Red[/]\
[b white], [/][bold #ff00ff]Magenta[/][b white], [/][bold #af00ff]Violet[/]\
[b white]][/]",
        subtitle_align="right",
    )
    example_console.print(panel1, justify="center")

    example_console.line(2)
    gradient2 = Gradient(
        lorem.paragraphs(4), rainbow=True, style="bold italic", justify="left"
    )
    panel2 = Panel(
        gradient2,
        title="[b u white]Rainbow Gradient[/]",
        subtitle="[white]rainbow = [/][b i #5f00ff]True[/]",
        subtitle_align="right",
        padding=(1, 4),
    )
    example_console.print(panel2, justify="center")
    example_console.save_svg(CWD / "Images" / "gradient_example.svg")
