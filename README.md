# wikinator

Convert Google docs into a markdown-based wiki.

**Note**: This is a work in progress, and not all features will be supported or working properly.

## tl;dr
[Install `uv`](https://docs.astral.sh/uv/getting-started/installation/) and then:
```
uvx wikinator --help
Usage: wikinator [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Display version and exit.
  -v         Show verbose logging.
  -vv        Show debug logging.
  -vvv       Show full trace logging.
  --help     Show this message and exit.

Commands:
  upload   Convert and upload a file hierarchy to a GraphQL wiki.
  convert  Given the URL of a specific gdoc:
  config   View or set configuration settings.
```

Given a directory, convert supported file types into markdown-based files while maintaining names and directory structure. This can then be uploaded into various wiki systems.

### Supported File Types
- DOCX files (default for GDocs) are converted to markdown
- images are extracted, uploaded and embedded in the markdown
- FUTURE `text` and code file types are wrapped in markdown code blocks
- FUTURE CSV and XSLT are converted to markdown tables
- FUTURE for any document that is converted to markdown, a copy of the original is uploaded and attached

### Supported Wiki Import
- wiki.js (and other GraphQL-based wikis)
- Obsidian

## Usage
```
uvx wikinator --help
uvx wikinator config

uvx wikinator convert https://gdoc/full/url --path=wiki/path
uvx wikinator convert sOmE-googleDoc-Id --path=wiki/path2

uvx wikinator upload target_dir
uvx wikinator upload target_file.md new/path
```

`convert` will take a single URL to a google doc, convert it to markdown, and
upload that to the configured GraphQL server using the title from the document.
An optional `path` option is provided to specify to path in the wiki to upload
the document to: `

`upload` loads a full directory into the wiki. In the above examples:
- Upload the directoy tree at `target_dir` into the wikipath `target_dir`
- Upload the file `target_file.docx` into the wiki path `new/path/target_file`

Assuming the `en` locale, the final paths in the wiki will be:
- $GRAPH_DB/en/target_dir/...
- $GRAPH_DB/en/new/path/target_file

## Configuration
There is nothing to install, the `wikinator` command can be run from anywhere [`uvx` is installed](https://docs.astral.sh/uv/getting-started/installation/).

To upload to your wiki, you must have:
1. the URL
2. an authentication token

Configuring the values in wikinator:
```
uvx wikinator config db_url https://db.example.com/graphql
uvx wikinator config db_token <authentication-token-for-your-graphdb>
```

When accessing Google docs, `wikinator` will confirm access to the requested files with a browser-based user authentication. These details will be stored in the configuration directory (`uvx wikinator config config_dir`) in `token.json` for future use.

Once this file is set up correctly, confirm with with, which should show a list of configuration settings (including the start and end characters of the API token):
```
uvx wikinator config
```

The `config` command will also display the location of the configuration file.

### wiki.js
This section is specific to the getting configuration values for a wiki.js server.

You'll need the URL of the server, and the [authentication token](https://docs.requarks.io/dev/api#authentication) for you account. For wiki.js, the API tokens are manged via Administration -> API Access, and a new token can be generated with "+ New API Key".

With both URL and API token, configure the `db_url` and `db_token` settings with the `wikinator config` command, as above.

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

## Release & Publish
To publish (to [PyPI](pypi.org), for `uvx`), a `UV_PUBLISH_TOKEN` is needed. [Create an API token](https://pypi.org/help/#apitoken) using a PyPI account, and store that in file named `.env` in the same directoy as the `Makefile`:
```
UV_PUBLISH_TOKEN=some-long-complicated-token-string
```

When ready to publish a release, [update the version](https://docs.astral.sh/uv/guides/package/#updating-your-version) and build the distribution:
```
new_version=`uv version --bump patch --short`
git commit -am "Releasing v$new_version"
git tag -a v$new_version -m "Version $new_version"
git push
make dist
```

**TODO**: Configure a GitHub Action for releases based on merges-to-main.

## Development Log
The development log will be kept here until the 1.0 release.

### 2026-03-23
Preparing v0.9.0 release.

With image upload, adding image compression:
- if an image is over 5M
- "optimize it" using 60% quality.

TODO for a v1.0 release:
- [ ] Add config settings and params for image resize (max size, quality)
- [ ] Make "embedded images" a configurable flag
- [ ] Refactor other commands to use new image system
- [ ] A few more simple tests
    - [ ] Test for doc with large images
- [ ] Cleanup and test commands:
    - [ ] upload : files to wiki
    - [ ] download : gdocs/wiki to file
    - [ ] convert : files to markdown files
    - [ ] ??? : single file, gdocs -> wiki (currently `convert`)

Post 1.0 possibilities:
- download search/spider: follow links, search parents, etc.
    - understand googledocs hierarchy/organization
- download HTML -> markdown:
    - flexible conversion systems mime-type => markdown

### 2026-03-21
And 22, the whole vernal eqinox weekend: Getting image upload working.

### 2026-03-20
Preparing for v0.9 release.

Changes:
- [x] Download DOCX instead of MD
- [x] Use docxit to extract MD
- [-] Pivot to image-dir (fullpath+'images')
    - [x] Update image names: `/full-path-file_name-image.jpg`
- [x] Get upload doc + images dir working - `/path/filename/imagename.jpg`
- [ ] Add image compress for anything 5M and over
- [ ] test and release -> v0.9

Image upload:
- https://github.com/requarks/wiki/discussions/6049
- https://github.com/requarks/wiki/issues/2413#issuecomment-689876881
- https://docs.requarks.io/guide/assets

```bash
# Source - https://stackoverflow.com/a/31988438
# Posted by Paul Bastide
# Retrieved 2026-03-19, License - CC BY-SA 3.0

curl -u "<EMAIL>:<PASSWORD>" -X POST -H "X-Update-Nonce: <NONCE>" -H "Content-Type: <CONTENT_TYPE>" -H "Slug: <FILENAME>" --data "@<FILE>" "https://<SERVER>/wikis/basic/api/wiki/<WIKI>/page/<WIKIPAGE>/feed?category=attachment"
```

`uv version --short` provides just the version from

Refactor doc upload to use an image dir (fullpath/images/...), and only resize images larget than 5Mb. -> v0.9

### 2026-03-19
Released v0.7, with `convert` command working:

First, configure your graphql wiki:
1. `uvx wikinator config db_url https://example.com/graphql`
2. `uvx wikinator config db_token long-API-token-for-graphql`

Then:

`uvx wikinator some-googledoc-id -path target/wiki/path`

This will confirm access to the supplied GoogleDoc ID, download and convert the document, than upload that document to "https://example.com/target/wiki/path/document-title".

Next step is an override confirmation (if that path already exists), and a `-y` option to skip the check. -> v0.8

Done and released. 0.8 in the wild.

### 2026-03-08
Adding `config` and `convert` commands.
- `config` helps manage config
- `convert` will read, convert and upload a google doc

### 2025-08-07
Refactored and disabled (for now) the convert, extract and teleport commands. The code remains in place, but the
current focus is on convert and upload to graphql, and I wan to disable any code that's not in that path while testing.

Added a verbose logging option, `-v`, to watch files being processed.

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

[^3]: At 25-08-10 19:35, Paul Philion said: This is a test comment.

I was able to get this working in sample code in a few hours.
