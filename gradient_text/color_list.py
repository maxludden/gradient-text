"""Generate a random spectrum of colors from the named color palette."""
# pylint: disable=E0401
from itertools import cycle
from random import randint
from typing import List

from rich.table import Table
from rich.text import Text

from gradient_text.color import Color
from gradient_text.log import get_console


class ColorList(list):
    """Generate a random spectrum of colors from the named color palette.""" ""

    colors: List[str] = [
        "magenta",
        "violet",
        "purple",
        "blue",
        "lightblue",
        "cyan",
        "lime",
        "yellow",
        "orange",
        "red",
    ]

    def __init__(self, invert: bool = False):
        super().__init__()
        self.color_list: List[Color] = []
        start_index = randint(0, 9)
        random_colors: List[str] = []
        step = -1 if invert else 1
        for index in range(10):
            current = start_index + (index * step)
            if current > 9:
                current -= 10
            if current < 0:
                current += 10
            random_colors.append(self.colors[current])
        color_cycle = cycle(random_colors)
        for _ in range(10):
            color = Color(next(color_cycle))
            self.color_list.append(color)
            if color is None:
                break

    def __call__(self):
        return self.color_list

    def __getitem__(self, index):
        return self.color_list[index]

    def __len__(self):
        return len(self.color_list)

    def __iter__(self):
        return iter(self.color_list)

    def reverse(self):
        self.color_list.reverse()

    def get_first_color(self):
        """Returns the first color in the list."""
        return self.color_list[0]

    def get_last_color(self):
        """Returns the last color in the list."""
        return self.color_list[-1]

    @classmethod
    def colored_title(cls) -> Text:
        """Returns `ColorList` title with colors applied."""
        title = [
            Text("C", style="bold.magenta"),
            Text("o", style="bold.violet"),
            Text("l", style="bold.purple"),
            Text("o", style="bold.blue"),
            Text("r", style="bold.lightblue"),
            Text("L", style="bold.cyan"),
            Text("i", style="bold.lime"),
            Text("s", style="bold.yellow"),
            Text("t", style="bold.orange"),
        ]
        return Text.assemble(*title)

    def __rich__(self) -> Table:
        table = Table(
            title=self.colored_title(),
            show_header=False,
            expand=False,
            padding=(0, 1),
        )
        for color in self.color_list:
            table.add_row(
                Text(str(color.name).capitalize(), style=f"bold {color.bg_style}")
            )
        return table


if __name__ == "__main__":
    console = get_console()
    color_list = ColorList(invert=True)
    console.line(2)
    console.print(color_list, justify="center")

    last_color = color_list.get_last_color()
    msg1 = f"[{last_color.style}]Last Color:[/]"  # ")
    msg2 = f"[bold {last_color.bg_style}]{str(last_color.name).capitalize()}[/]"
    console.print(
        f"{msg1} {msg2}",
        justify="center",
    )
