from pathlib import Path

from wikinator.page import Page

def test_something():
    # need test docs to test convert
    pass


def test_page():
    # load a page
    page = Page.load_file(Path("tests/resources/test.docx"))
    assert page is not None
    assert page.path == "tests/resources/test"