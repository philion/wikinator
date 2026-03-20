import json
from pathlib import Path
import logging
import re


log = logging.getLogger(__name__)


class Page:
    """
    Specific class for page, to help with validation, as graphql is strict about params
    """
    id: int
    content: str
    editor: str
    isPublished: bool
    isPrivate: bool
    locale: str
    path: str
    tags: list[str]
    title: str
    description: str


    def __init__(self, id: int, content: str, editor: str, isPublished: bool, isPrivate: bool,
                locale: str, path: str, tags: list[str], title: str, description: str):
        self.id = id
        self.content = content
        self.editor = editor
        self.isPublished = isPublished
        self.isPrivate = isPrivate
        self.locale = locale
        self.path = path
        self.tags = tags
        self.title = title
        self.description = description
        self.comments = []


    @classmethod
    def load(cls, params: dict[str,any]):
        return cls(
            id = params.get("id"),
            content = params.get("content"),
            editor  = params.get("editor"),
            isPublished = params.get("isPublished"),
            isPrivate = params.get("isPrivate"),
            locale = params.get("locale"),
            path = params.get("path"),
            tags = params.get("tags", ["gdocs"]),
            title = params.get("title"),
            description = params.get("description"),
        )


    @classmethod
    def load_json(cls, json_str:str):
        return cls.load(cls, json.loads(json_str))


    @classmethod
    def load_file(cls, filename:Path):
        path = filename
        name = path.stem
        ext = path.suffix.lower()
        path_name = Path(path.parent, name)

        # TODO - implement
        # read the file as markdown
        # check for metadata header and file-on-disk metadate
        # for creating page struct

        file_mode = 'r'
        if ext == ".docx":
            file_mode = 'rb'

        with open(filename, file_mode) as file:
            content = file.read()

        return cls(
            id = -1, # loaded from file
            content = content,
            editor  = "markdown",
            isPublished = True,
            isPrivate = True,
            locale = "en",
            path = str(path_name),
            tags = "",
            title = name,
            description = "", # metadata
        )


    def __str__(self):
        return f'Page({self.id} {self.path} {self.title})'

    # Make sure a string
    def url_safe(self, value: str) -> str:
        value = value.strip()
        value = value.lower()
        value = re.sub(r"[^a-zA-Z0-9-._~]", "-", value)
        value = re.sub(r"-+", "-", value)
        return value


    def fullpath(self, path:str) -> str:
        full = self.url_safe(self.path)

        if path:
            return path + '/' + full
        else:
            return full


    def filename(self, root = None) -> Path:
        """
        determine the file name for this page
        If `root` is supplied, that file name
        will be realtive to that path
        """
        # replace chars in path
        filename = self.fullpath(root) + '.md'
        return Path(filename)


    def update_path(self, root: str):
        if root and len(root) > 0:
            self.path = self.fullpath(root)


    def write_file(self, filename:str) -> None:
        """
        write content and metadata to specified file
        """
        target = Path(filename)

        # assure required dirs exist
        target.parent.mkdir(parents=True, exist_ok=True)

        # write the content
        with open(target, 'w') as output_file:
            # TODO write yaml-based meta data
            output_file.write(self.content)


    def write(self, root:str) -> None:
        """
        Output the converted document to the specified directory `root`.
        Use the stored path to output relative to the provided root.
        """
        filename = self.filename(root)
        log.info(f"writing {filename}")
        self.write_file(filename)


    def append_comment(self, comment) -> None:
        self.comments.append(comment)


    def vars(self):
        temp = vars(self)
        del temp["comments"]
        return temp