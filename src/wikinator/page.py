import json
from pathlib import Path
import logging
import re
import os


log = logging.getLogger(__name__)

MIMETYPES = {
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.md':   'text/markdown',
    '.apng':  'image/apng', # Animated Portable Network Graphics (APNG)
    '.avif':  'image/avif', # AV1 Image File Format (AVIF)
    '.gif':   'image/gif',  # Graphics Interchange Format (GIF)
    '.jpeg':  'image/jpeg', # Joint Photographic Expert Group image (JPEG)
    '.jpg':   'image/jpeg', # Joint Photographic Expert Group image (JPEG)
    '.png':   'image/png',  # Portable Network Graphics (PNG)
    '.svg':   'image/svg+xml', # Scalable Vector Graphics (SVG)
    '.webp':  'image/webp', # Web Picture format (WEBP)
}
def mimetype_from_name(name:str) -> str:
    _, ext = os.path.splitext(name)
    ext = ext.lower()
    if ext in MIMETYPES:
        return MIMETYPES[ext]
    else:
        log.warning(f"Unrecognized extention: {ext}, from {name}")
        return None


class PageImage:
    name: str
    content: bytes

    def __init__(self, name, content):
        self.name = name
        self.content = content

    @property
    def mimetype(self):
        return mimetype_from_name(self.name)


class Page:
    """
    Specific class for page, to help with validation, as graphql is strict about params
    """
    id: int
    content: bytes
    editor: str
    isPublished: bool
    isPrivate: bool
    locale: str
    path: str
    tags: list[str]
    title: str
    description: str

    # When Page is constructed, it needs to have the wiki target path
    def __init__(self, id: int, content: bytes, editor: str, isPublished: bool, isPrivate: bool,
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
        self.images = {}
        self.isImageEmbedded = False


    @classmethod
    def load(cls, params: dict[str,any]):
        return cls(
            id = params.get("id", 0),
            content = params.get("content"),
            editor  = params.get("editor", "markdown"),
            isPublished = params.get("isPublished", False),
            isPrivate = params.get("isPrivate", False),
            locale = params.get("locale", "en"),
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
    @staticmethod
    def url_safe(value: str) -> str:
        value = value.strip()
        value = value.lower()
        value = re.sub(r'[^a-zA-Z0-9-._~/]', '-', value)
        value = re.sub(r"-+", "-", value)
        return value


    def fullpath(self, path:str) -> str:
        if path:
            fullpath = str(Path(path, self.path))
        else:
            fullpath = self.path

        return self.url_safe(fullpath)


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
        del temp["images"]
        return temp


    def add_image(self, rId:str, image:PageImage):
        if rId and image:
            self.images[rId] = image


    def get_image(self, rId:str) -> PageImage:
        return self.images[rId]


    def get_image_path(self, rId:str) -> str:
        # ASSUMPTION: At some point, document 'path' must be set to upload-path/filename (no ext)
        # image location: /upload/path/file_name/images/image_name
        # That's the ideal. For now, managing folders in wiki.js is a mess, and it's easier
        # to futz with the path as a single long name:
        #    upload-path-file_name-image_name.jpg
        image = self.get_image(rId)
        if image:
            #path = str(Path(self.path, image.name))
            path = self.path.replace('/', '-') + '-' + image.name
            log.warning(f"---- {path}")
            path = path.strip('-')
            return '/' + path
        else:
            # no rId
            return None


    def get_image_link(self, rId:str) -> str:
        """Generate a link to an image, depending on the isImageEmbedded flag"""
        # generate internal image name, based on resource ID
        if self.isImageEmbedded:
            return f"![][image{rId[3:]}]"
        else:
            # use image and document metadata to generate a value link with URL
            # ASSUMPTION: At some point, document 'path' must be set to upload-path/filename (no ext)
            # image location: /upload/path/file_name/images/image_name
            image = self.get_image(rId)
            alt_text = ""
            path = self.get_image_path(rId)
            if image:
                return f"![{alt_text}]({path})"
            else:
                # no rId
                return None
