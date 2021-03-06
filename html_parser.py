from __future__ import annotations

from typing import Dict, List, Tuple


class Text:
    def __init__(self, text: str, parent: Node):
        self.text = text
        self.children: List[Node] = []
        self.parent = parent

    def __repr__(self) -> str:
        return repr(self.text)


class Element:
    def __init__(self, tag: str, attributes: Dict[str, str], parent: Node | None):
        self.tag = tag
        self.attributes = attributes
        self.children: List[Node] = []
        self.parent = parent

    def __repr__(self) -> str:
        attrs = [" " + k + '="' + v + '"' for k, v in self.attributes.items()]
        return "<" + self.tag + "".join(attrs) + ">"


Node = Text | Element


def print_tree(node: Node, indent: int = 0) -> None:
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)


class HTMLParser:
    def __init__(self, body: str):
        self.body = body
        self.unfinished: List[Element] = []

    def parse(self) -> Node:
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

    def get_attributes(self, text: str) -> Tuple[str, Dict[str, str]]:
        parts = text.split()
        tag = parts[0].lower()
        attributes: Dict[str, str] = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", '"']:
                    value = value[1:-1]
                attributes[key.lower()] = value
            else:
                attributes[attrpair.lower()] = ""
        return tag, attributes

    def add_text(self, text: str) -> None:
        if text.isspace():
            return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    SELF_CLOSING_TAGS = [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]

    def add_tag(self, tag: str) -> None:
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"):
            return
        self.implicit_tags(tag)

        if tag.startswith("/"):
            if len(self.unfinished) == 1:
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None  # type: ignore
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    HEAD_TAGS = [
        "base",
        "basefont",
        "bgsound",
        "noscript",
        "link",
        "meta",
        "title",
        "style",
        "script",
    ]

    def implicit_tags(self, tag: str | None) -> None:
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif (
                open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS
            ):
                self.add_tag("/head")
            else:
                break

    def finish(self) -> Node:
        if len(self.unfinished) == 0:
            self.add_tag("html")
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
