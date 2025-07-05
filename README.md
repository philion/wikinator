# wikinator

Convert a Google drive download into a markdown-based wiki.

## tl;dr
```
uvx wikinator -src some/dir -dest another_dir
uvx wikinator -src some/dir -graphql https://wiki.example.com/graphql -token 'graphql-auth-token'
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


**Note**: This is a work in progress, and not all features will be supported or working properly.

The development log will be kept here until the 1.0 release.


## Usage
```
uvx wikinator -src some/dir -dest another_dir
uvx wikinator -src some/dir -graphql https://wiki.example.com/graphql -token 'graphql-auth-token'
```

## Install

1. Install dependencies


## Build & Test
1. Clone
    ```
    git clone ...
    ```
2. Run, with uv
    ```
    uv run -m wikinator [options]
    ```
3. Test, with pytest
    ```
    uv run pytest
    ```

## Development Log

### 2025-07-04
Let's make a project! Today's goals:
- [*] clean up code and README
- [ ] add CLI options, using type (not all implemented)
- [ ] initial commit to github
- [ ] add image handling
- [ ] upload to pypi and confirm uvx commands

Cruft removed. README updated. (author waves, breaking 4th wall)

Moving on the main() cleanup and adding support for https://github.com/fastapi/typer


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
