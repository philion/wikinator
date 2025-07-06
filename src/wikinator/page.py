import json
from pathlib import Path
import logging


log = logging.getLogger(__name__)


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

    @classmethod
    def load_file(cls, filename:str):
        # TODO - implement
        # read the file as markdown
        # check for metadata header and file-on-disk metadate
        # for creating page struct
        return cls(
            content = "",# file
            editor  = "markdown",# metadata
            isPublished = False,# metadata
            isPrivate = True,# metadata
            locale = "en",# metadata
            path = "",# from filename
            tags = "",# metadata
            title = "",# metadata
            description = "", # metadata
        )

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
