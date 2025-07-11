# wikinator

Convert a Google drive download into a markdown-based wiki.

**Note**: This is a work in progress, and not all features will be supported or working properly.

## tl;dr
```
uvx wikinator some/dir another_dir
uvx wikinator some/dir -graphql https://wiki.example.com/graphql -token 'graphql-auth-token'
```

Given a directory, convert supported file types into markdown-based files while maintaining names and directory structure. This can then be uploaded into various wiki systems.

### Supported File Types
- DOCX files (default for GDocs) are converted to markdown
- images are extracted, uploaded and embedded in the markdown
- `text` and code file types are wrapped in markdown code blocks
- CSV and XSLT are converted to markdown tables
- for any document that is converted to markdown, a copy of the original is uploaded and attached

### Supported Wiki Import
- wiki.js (and other GraphQL-based wikis)
- Obsidian

The development log will be kept here until the 1.0 release.

## Usage
```
uvx wikinator convert some/dir another_dir
uvx wikinator extract target_dir
uvx wikinator upload target_dir wikipath
uvx wikinator teleport wikipath
```

`convert` converts directory full of DOCX into markdown.

`extract` extracts the docs from google docs as markdown.

`upload` loads a full directory into wiki.js

`teleport` goes directly from google drive to wiki.js.

TODO: Details on setting up creds for google docs and wikijs.

## Build & Test
1. Clone
    ```
    git clone https://github.com/philion/wikinator.git
    cd wikinator
    ```
2. Run, with uv
    ```
    uv run wikinator [options]
    ```
3. Test, with pytest
    ```
    uv run pytest
    ```

## Development Log

### 2025-07-08
Initial (buggy, probably) implementation of the full command set:
- `convert` converts directory full of DOCX into markdown.
- `extract` extracts the docs from google docs as markdown.
- `upload` loads a full directory into wiki.js
- `teleport` goes directly from google drive to wiki.js.

### 2025-07-07
Decent progress with google drive download. Still lots of problems.
- [ ] get single file and dir params working.
- [x] fix `\n` translation problem. where are they coming from
- [ ] for single input file, assume single output filename (if doen't exists). if does, and is dir, write -in-.
- [x] simple formatting tests
- [ ] research which converter google is using

pandoc doesn't do embedding the same way (HTML-only): https://pandoc.org/MANUAL.html#option--embed-resources%5B


### 2025-07-06
Getting into formatting details, and I want to decompse and stream-line the docxit converter.
- [x] docxit creates in memory
- [x] better page handling, read and write files to disk
- [x] get first test working
- [x] simple formatting tests
- [x] build commands (unimplemented)
- [ ] for single input file, assume single output filename (if doen't exists). if does, and is dir, write -in-.

Let's combine testing lists with a simple test:
- load a file with a list
- convert
- confirm it contains the correct list

Moved the code around to simplify and remove potential circular dependencies.

Code runs as expected, as does trival test case.

Bumping version to 0.5, but not yet ready to release.

Thinking about commands:
- convert : files -> files
- extract : from googledocs -> file system
- upload  : from files -> graphql
- teleport : from googledoc -> graphql

Refactored __main__ to better commands. Got `-v` working.

Original behavior is working as `wikinator convert`.

Now looking at extract command.


### 2025-07-05
Starting work on image preservation.

Looking first at https://github.com/haesleinhuepf/docx2markdown for images.

Created a `Docx2MarkdownConverter` which almost works: images are put in the wrong path in the MD (`s/images/` instead of just `images`).
There's probably an easy fix, but lets try a pandoc version.

Creating `PandocConverter` to try and compare output.
```
pandoc {indoc} -f docx -t markdown --wrap=none --markdown-headings=atx --extract-media=images -o {outdoc}
```

Neither produces desired results.

Trying a literal hack of docx2markdown, to see how quickly I can fix the little problems I saw.

Got it working quickly, removed a little bug, got the images.

Now looking over the DOCX XML format to see how much I can scrape out.

https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.fontsizecomplexscript?view=openxml-3.0.1

Added detection for strikethru and Courier New (as "code font").

This is good enough for v0.2!

Oops. minor bug. fixing with v0.3

Noticed when working on strikethru that nested lists didn't seem to be working.

Next tasks:
- [x] List handling
- [x] Code cleanup (remove unused libs)
- [ ] restructure docxit for in-memory
- [ ] simple testing.
- [x] recognize and handle single file
- [x] default output to local dir

Looking over the raw XML, it looks like...
```xml
<w:numPr>
    <w:ilvl w:val="0" />
    <w:numId w:val="2" />
</w:numPr>
```
It looks like:
* `w:ilvl` is the zero-based indent level
* `w:numId` is an ID from numbering.xml, roughly mapping to:
    - val=1 ordered list: `1. `
    - val=2 checklist: `- [ ]`
    - val=3 bullet: `* `

Restructured and cleaned up. Removed unneeded code and libraried.

Created a simple docx doc for testing.

Far enough that a new release feels right. v0.4!


### 2025-07-04
Let's make a project! Today's goals:
- [x] clean up code and README
- [x] add CLI options, using type (not all implemented)
- [x] initial commit to github
- [ ] add image handling
- [x] upload to pypi and confirm uvx commands

Cruft removed. README updated. (author waves, breaking 4th wall)

Moving on the main() cleanup and adding support for https://github.com/fastapi/typer

Added simple CLI options for src and dest. Got end-to-end tree processing.

Added Makefile to help with release management. Got PyPI setup: https://pypi.org/project/wikinator/

`uvx wikinator` is working.

Let's go for git and call it a day!

### 2025-07-03
Next steps are testing different document converters and accessing google drive via API.

#### Markdown conversion libraries
- pandoc, see https://docs.asciidoctor.org/asciidoctor/latest/migrate/ms-word/
- markitdown, https://github.com/microsoft/markitdown
- docx2markdown, https://github.com/haesleinhuepf/docx2markdown
- docx2md, https://github.com/mattn/docx2md

Reference:
- https://www.docstomarkdown.pro/convert-word-or-docs-to-markdown-using-pandoc/

#### Google Drive API
Starting with https://developers.google.com/workspace/drive/api/quickstart/python

> Note: Follow those Google directions for setting up everything. It's complicated compared to simply generating a service token. Your intrepid author made different tokens in different accounts and couldn't access anything! And get permissions right! Document specific needs in intstall docs.

Further aside: There are two versions of the tool: file-based and google-takeout. The google related stuff will always be a bear to setup.

Made suffienct progress to feel like there a seperate CLI tool here. Set aside for now, and focus on:
1. Build file-based output
2. Generate and link images
3. Clean up for initial 0.1 version

### 2025-07-02
Initial time-boxed work started to examine what would be required to migrate our existing GoogleDocs-based info repo into a wiki, with wiki.js being targeted.

Initial proof-of-concept goals:
- Convert a docx page to md or asciidoc
- Upload test pages to wiki.js

I was able to get this working in sample code in a few hours.
