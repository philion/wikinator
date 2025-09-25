# Tests for the docxit DOCX -> marldown converter
from pathlib import Path

from wikinator import docxit

def test_basic_formatting():
    # load file
    test_file = Path("tests/resources/Document.docx")
    #test_out = Path("out")
    #root = Path("tests")

    # convert
    # docx_file:Path, root:Path, outroot:Path

    page = docxit.convert(test_file)

    # validate
    assert page is not None
    assert len(page.content) > 0

    assert page.title == "Document"
