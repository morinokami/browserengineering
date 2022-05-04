import pytest

from html_parser import HTMLParser, print_tree


def test_html_parser(capsys: pytest.CaptureFixture[str]) -> None:
    parser = HTMLParser("<html><body>test</body></html>")
    print_tree(parser.parse())
    captured = capsys.readouterr()
    assert (
        captured.out
        == """ <html>
   <body>
     'test'
"""
    )

    parser = HTMLParser("test")
    print_tree(parser.parse())
    captured = capsys.readouterr()
    assert (
        captured.out
        == """ <html>
   <body>
     'test'
"""
    )

    parser = HTMLParser("<body>test")
    print_tree(parser.parse())
    captured = capsys.readouterr()
    assert (
        captured.out
        == """ <html>
   <body>
     'test'
"""
    )

    parser = HTMLParser("<base><basefont></basefont><title></title><div></div>")
    print_tree(parser.parse())
    captured = capsys.readouterr()
    assert (
        captured.out
        == """ <html>
   <head>
     <base>
     <basefont>
     <title>
   <body>
     <div>
"""
    )

    parser = HTMLParser("<div>text")
    print_tree(parser.parse())
    captured = capsys.readouterr()
    assert (
        captured.out
        == """ <html>
   <body>
     <div>
       'text'
"""
    )

    parser = HTMLParser("<div name1=value1 name2=value2>text</div")
    print_tree(parser.parse())
    captured = capsys.readouterr()
    assert (
        captured.out
        == """ <html>
   <body>
     <div name1="value1" name2="value2">
       'text'
"""
    )
