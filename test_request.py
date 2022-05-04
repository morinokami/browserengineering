# mypy: ignore-errors

import test

import pytest

from request import request, show

test.socket.patch().start()
test.ssl.patch().start()


def test_show(capsys: pytest.CaptureFixture[str]) -> None:
    show("<body>hello</body>")
    captured = capsys.readouterr()
    assert captured.out == "hello"

    show("he<body>llo</body>")
    captured = capsys.readouterr()
    assert captured.out == "hello"

    show("he<body>l</body>lo")
    captured = capsys.readouterr()
    assert captured.out == "hello"

    show("he<body>l<div>l</div>o</body>")
    captured = capsys.readouterr()
    assert captured.out == "hello"

    show("he<body>l</div>lo")
    captured = capsys.readouterr()
    assert captured.out == "hello"

    show("he<body>l<div>l</body>o</div>")
    captured = capsys.readouterr()
    assert captured.out == "hello"


def test_request() -> None:
    url = "http://test.test/example1"
    test.socket.respond(url, b"HTTP/1.0 200 OK\r\nHeader1: Value1\r\n\r\nBody text")
    headers, body = request(url)
    assert (
        test.socket.last_request(url)
        == b"GET /example1 HTTP/1.0\r\nHost: test.test\r\n\r\n"
    )
    assert headers == {"header1": "Value1"}
    assert body == "Body text"

    url = "http://test.test/te"
    test.socket.respond(
        url, b"HTTP/1.0 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n"
    )
    assert test.errors(request, url)

    url = "http://test.test/ce"
    test.socket.respond(
        url, b"HTTP/1.0 200 OK\r\nContent-Encoding: gzip\r\n\r\n\x00\r\n\r\n"
    )
    assert test.errors(request, url)


def test_ssl_support() -> None:
    url = "https://test.test/example2"
    test.socket.respond(url, b"HTTP/1.0 200 OK\r\n\r\n")
    header, body = request(url)
    assert body == ""

    url = "https://test.test:400/example3"
    test.socket.respond(url, b"HTTP/1.0 200 OK\r\n\r\nHi")
    header, body = request(url)
    assert body == "Hi"

    assert test.errors(request, "https://test.test:401/example3")
