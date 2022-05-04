from __future__ import annotations

import tkinter
import tkinter.font
from typing import List, Literal, Optional, Tuple

from font import get_font
from html_parser import Element, HTMLParser, Node, Text
from request import request

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

BLOCK_ELEMENTS = [
    "html",
    "body",
    "article",
    "section",
    "nav",
    "aside",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hgroup",
    "header",
    "footer",
    "address",
    "p",
    "hr",
    "pre",
    "blockquote",
    "ol",
    "ul",
    "menu",
    "li",
    "dl",
    "dt",
    "dd",
    "figure",
    "figcaption",
    "main",
    "div",
    "table",
    "form",
    "fieldset",
    "legend",
    "details",
    "summary",
]


def layout_mode(node: Node) -> Literal["block", "inline"]:
    if isinstance(node, Text):
        return "inline"
    elif node.children:
        for child in node.children:
            if isinstance(child, Text):
                continue
            if child.tag in BLOCK_ELEMENTS:
                return "block"
        return "inline"
    else:
        return "block"


class BlockLayout:
    def __init__(
        self,
        node: Node,
        parent: DocumentLayout | BlockLayout,
        previous: Optional[DocumentLayout | BlockLayout | InlineLayout],
    ):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children: List[BlockLayout | InlineLayout] = []
        self.x: Optional[int] = None
        self.y: Optional[int] = None
        self.width: Optional[int] = None
        self.height: Optional[int] = None

    def layout(self) -> None:
        previous = None
        for child_node in self.node.children:
            next: BlockLayout | InlineLayout
            if layout_mode(child_node) == "inline":
                next = InlineLayout(child_node, self, previous)
            else:
                next = BlockLayout(child_node, self, previous)
            self.children.append(next)
            previous = next

        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            assert self.previous.y is not None
            assert self.previous.height is not None
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        for child in self.children:
            child.layout()

        self.height = sum(
            [child.height if child.height else 0 for child in self.children]
        )

    def paint(self, display_list: List[DrawText | DrawRect]) -> None:
        for child in self.children:
            child.paint(display_list)


class InlineLayout:
    def __init__(
        self,
        node: Node,
        parent: DocumentLayout | BlockLayout,
        previous: Optional[DocumentLayout | BlockLayout | InlineLayout],
    ):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children: List[BlockLayout | InlineLayout] = []
        self.x: Optional[int] = None
        self.y: Optional[int] = None
        self.width: Optional[int] = None
        self.height: Optional[int] = None
        self.display_list: Optional[
            List[Tuple[int, float, str, tkinter.font.Font]]
        ] = None
        self.cursor_x: Optional[int] = None
        self.cursor_y: Optional[float] = None

    def layout(self) -> None:
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            assert self.previous.y is not None
            assert self.previous.height is not None
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        self.display_list = []
        self.weight: Literal["normal", "bold"] = "normal"
        self.style: Literal["roman", "italic"] = "roman"
        self.size = 16

        self.cursor_x = self.x
        self.cursor_y = self.y
        self.line: List[Tuple[int, str, tkinter.font.Font]] = []
        self.recurse(self.node)
        self.flush()

        assert self.cursor_y is not None
        assert self.y is not None
        self.height = self.cursor_y - self.y

    def recurse(self, tree: Node) -> None:
        if isinstance(tree, Text):
            self.text(tree)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

    def open_tag(self, tag: str) -> None:
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()

    def close_tag(self, tag: str) -> None:
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.flush()
            assert self.cursor_y is not None
            self.cursor_y += VSTEP

    def text(self, node: Text) -> None:
        font = get_font(self.size, self.weight, self.style)
        for word in node.text.split():
            w = font.measure(word)
            assert self.cursor_x is not None
            if self.cursor_x + w > WIDTH - HSTEP:
                self.flush()
            self.line.append((self.cursor_x, word, font))
            self.cursor_x += w + font.measure(" ")

    def flush(self) -> None:
        if not self.line:
            return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        assert self.cursor_y is not None
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            assert self.display_list is not None
            self.display_list.append((x, y, word, font))
        self.cursor_x = HSTEP
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

    def paint(self, display_list: List[DrawText | DrawRect]) -> None:
        if isinstance(self.node, Element) and self.node.tag == "pre":
            assert self.x is not None
            assert self.y is not None
            assert self.width is not None
            assert self.height is not None
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, "gray")
            display_list.append(rect)
        assert self.display_list is not None
        for x, y, word, font in self.display_list:
            display_list.append(DrawText(x, y, word, font))


class DocumentLayout:
    def __init__(self, node: Node):
        self.node = node
        self.parent = None
        self.previous = None
        self.children: List[BlockLayout | InlineLayout] = []

    def layout(self) -> None:
        child = BlockLayout(self.node, self, None)
        self.children.append(child)

        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        assert child.height is not None
        self.height = child.height + 2 * VSTEP

    def paint(self, display_list: List[DrawText | DrawRect]) -> None:
        self.children[0].paint(display_list)


class DrawText:
    def __init__(self, x1: float, y1: float, text: str, font: tkinter.font.Font):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font

        self.bottom = y1 + font.metrics("linespace")

    def execute(self, scroll: float, canvas: tkinter.Canvas) -> None:
        canvas.create_text(
            self.left,
            self.top - scroll,
            text=self.text,
            font=self.font,
            anchor="nw",
        )

    def __repr__(self) -> str:
        return "DrawText(top={} left={} bottom={} text={} font={})".format(
            self.top, self.left, self.bottom, self.text, self.font
        )


class DrawRect:
    def __init__(self, x1: float, y1: float, x2: float, y2: float, color: str):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color

    def execute(self, scroll: float, canvas: tkinter.Canvas) -> None:
        canvas.create_rectangle(
            self.left,
            self.top - scroll,
            self.right,
            self.bottom - scroll,
            width=0,
            fill=self.color,
        )

    def __repr__(self) -> str:
        return "DrawRect(top={} left={} bottom={} right={} color={})".format(
            self.top, self.left, self.bottom, self.right, self.color
        )


class Browser:
    def __init__(self) -> None:
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()

        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.display_list: List[DrawText | DrawRect] = []

    def load(self, url: str) -> None:
        headers, body = request(url)
        self.nodes = HTMLParser(body).parse()
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()

    def draw(self) -> None:
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll, self.canvas)

    def scrolldown(self, e) -> None:  # type: ignore
        max_y = self.document.height - HEIGHT
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()


if __name__ == "__main__":
    import sys

    Browser().load(sys.argv[1])
    tkinter.mainloop()
