import os
from pathlib import Path, PurePath
import logging
import json

from markitdown import MarkItDown

import typer

class Page:
    """
    Specific class for page, to help with validation, as graphql is strict about params
    """
    content: str
    editor: str
    isPublished: bool
    isPrivate: bool
    locale: str
    path: str
    tags: list[str]
    title: str
    description: str

    def __init__(self, content: str, editor: str, isPublished: bool, isPrivate: bool,
                locale: str, path: str, tags: list[str], title: str, description: str):
        self.content = content
        self.editor = editor
        self.isPublished = isPublished
        self.isPrivate = isPrivate
        self.locale = locale
        self.path = path
        self.tags = tags
        self.title = title
        self.description = description

    @classmethod
    def load(cls, params: dict[str,any]):
        return cls(
            content = params["content"],
            editor  = params["editor"],
            isPublished = params["isPublished"],
            isPrivate = params["isPrivate"],
            locale = params["locale"],
            path = params["path"],
            tags = params["tags"],
            title = params["title"],
            description = params["description"],
        )

    @classmethod
    def load_json(cls, json_str:str):
        return cls.load(cls, json.loads(json_str))

    def write(self, root:str) -> None:
        """
        Output the converted document to the specified directory `root`.
        Use the stored path to output relative to the provided root.
        """
        filename = self.path + '.md'
        target = Path(root, filename)
        # assure required dirs exist
        target.parent.mkdir(parents=True, exist_ok=True)
        # write the content
        with open(target, 'w') as output_file:
            # TODO write yaml-based meta data?
            output_file.write(self.content)


class Converter:
    root: Path # Root for file walk, and to resolve rol paths

    def _convert(self, infile:Path) -> Page:
        raise NotImplementedError

    def convert(self, infile:Path, outroot:Path) -> Page:
        # translate with subclass
        new_doc = self._convert(infile)

        #print("converted", infile, new_doc.path)

        # write!
        new_doc.write(outroot)

        return new_doc

    def convert_directory(self, inpath:str, outroot:str):
        # load queues
        #docx_queue: list[Path] = []
        self.root = Path(inpath)

        for root, dirs, files in os.walk(self.root):
            for file in files:
                full_path = Path(root, file)
                ext = full_path.suffix.lower() # TODO strip first char, '.'

                # TODO: generic mapping to queue based on ext.
                if ext == ".docx":
                    #docx_queue.append(full_path) # TODO async!
                    self.convert(full_path, outroot)
                else:
                    logging.debug(f"No processor for {ext}, skipping {full_path}")


class MarkitdownConverter(Converter):
    def _convert(self, filepath:Path) -> Page:
        """
        Converts a markdown file into a struct to add to the wiki
        """
        md = MarkItDown(enable_plugins=False)
        result = md.convert(filepath)

        # determine the relative file path
        # this *includes* the top-level directly name
        rel_path = PurePath(os.path.relpath(filepath, self.root.parent)) # remove .parent to remove top dirname
        rel_file = PurePath(rel_path.parent, filepath.stem)

        return Page(
            title = result.title if result.title else filepath.stem,
            path = str(rel_file),
            content = result.text_content,
            editor = "markdown",
            locale = "en",
            tags = None,
            description = f"generated from: {filepath}",
            isPublished = False,
            isPrivate = True,
        )

        # trying to make everything async
        # skipping for now
        # start workers
        # with multiprocessing.Pool(3) as worker_pool:
        #     # create a list the same size for starmap
        #     args = [(doc, outroot) for doc in docx_queue]
        #     # run the workers
        #     results = worker_pool.starmap(convert_docx, args)
        #     # check result success
        #     for result in results:
        #         print(result)


def do_convert(src: str, dest: str) -> None:
    MarkitdownConverter().convert_directory(src, dest)


def main() -> None:
    typer.run(do_convert)


if __name__ == "__main__":
    main()
