import tkinter
from typing import List, Tuple

from request import request

DisplayList = List[Tuple[int, int, str]]

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100


def lex(body: str) -> str:
    text = ""
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            text += c
    return text


def layout(text: str) -> DisplayList:
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list


class Browser:
    def __init__(self) -> None:
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()

        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)

    def load(self, url: str) -> None:
        headers, body = request(url)
        text = lex(body)
        self.display_list = layout(text)
        self.draw()

    def draw(self) -> None:
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrolldown(self, e) -> None:  # type: ignore
        self.scroll += SCROLL_STEP
        self.draw()


if __name__ == "__main__":
    import sys

    Browser().load(sys.argv[1])
    tkinter.mainloop()
