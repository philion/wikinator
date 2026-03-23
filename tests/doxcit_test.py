# Tests for the docxit DOCX -> marldown converter
from io import StringIO
import logging
from pathlib import Path

import docx

from wikinator import docxit

log = logging.getLogger(__name__)

def test_basic_formatting():
    # load file
    test_file = Path("tests/resources/test3.docx")

    page = docxit.convert_file(test_file)

    # validate
    assert page is not None
    assert len(page.content) > 0

    assert page.title == test_file.stem

    # REMOVE: write the file to see what's in content, to write tests about what's expected
    #with open(page.title + '.md', "w") as md_file:
    #    md_file.write(page.content)


def test_numbering_cache():
    # load file
    test_file = Path("tests/resources/bullet-test.docx")
    doc = docx.Document(test_file)
    cache = docxit.build_numbering_cache(doc)

    # for id, val in cache.numbering.items():
    #     for lvl, numbering in val.items():
    #         log.warning(f">>>> {id}{type(id)},{lvl}{type(lvl)}: {numbering}")

    check = cache.get(1, 0)
    assert check is not None


def test_bullets():
    expected_lines = {
        1: "**Experiment",
        3: "1. After deploying",
    }
    # load file
    test_file = Path("tests/resources/bullet-test.docx")

    page = docxit.convert_file(test_file)

    # validate
    assert page is not None
    assert len(page.content) > 0

    assert page.title == test_file.stem

    buf = StringIO(page.content)
    lineno = 0
    for line in buf.readlines():
        lineno += 1

        #log.warning(f"### {lineno}: {line}")
        #log.warning(f"{lineno}: {line}")
        if lineno in expected_lines:
            expected = expected_lines[lineno]
            assert line.startswith(expected), f"expect '{expected}' at beginning of '{line}'"
