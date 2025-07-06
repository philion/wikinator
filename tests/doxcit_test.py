# Tests for the docxit DOCX -> marldown converter
from pathlib import Path

from wikinator.docxit import convert

def test_basic_formatting():
    # load file
    test_file = Path("tests/resources/test.docx")
    test_out = Path("out")
    root = Path("tests")

    # convert
    # docx_file:Path, root:Path, outroot:Path
    page = convert(test_file, root, test_out)

    # validate
    assert page is not None
    assert len(page.content) > 0
