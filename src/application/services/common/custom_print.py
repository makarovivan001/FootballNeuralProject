import sys

from domain.enums.print_colors import TextColor, BackgroundColor


class cprint:
    RESET = "\033[0m"

    def __init__(
            self,
            *args: list[str] | str,
            end='\n',
            sep=' ',
            color="",
            backgroud=""
    ):
        custom_text = (color + backgroud) + sep.join(map(str, args)) + self.RESET + end
        sys.stdout.write(custom_text)