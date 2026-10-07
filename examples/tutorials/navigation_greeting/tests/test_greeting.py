from greeting import greet


def test_greet():
    assert greet("Ada") == "Hello, Ada"
    assert greet("") == "Hello, "
