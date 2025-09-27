# Tests for the docxit DOCX -> marldown converter
from pathlib import Path

from wikinator import docxit

def test_basic_formatting():
    # load file
    test_file = Path("tests/resources/test3.docx")

    page = docxit.convert(test_file)

    # validate
    assert page is not None
    assert len(page.content) > 0

    assert page.title == test_file.stem

    # REMOVE: write the file to see what's in content, to write tests about what's expected
    with open(page.title + '.md', "w") as md_file:
        md_file.write(page.content)
