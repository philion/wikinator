
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

def subpath(path:Path, root:Path) -> str:
    """
    Given a path and a root, determine the subpath of that path relative to the root
    path: /some/full/path/to/a/file
    root: /some/full/path
    result: to/a/file
    """
    # NOTE: Adding trailing '/' removes leading / from local_path.
    # Otherwise /local/path is interpreted as absolute
    return path.replace(str(root.absolute()) + "/", "")
    # FIXME: try relative()


def repath(path:Path, old_root:Path, root:Path) -> Path:
    """
    Given a path, an old_root and a new_root, determine a new path.
    """
    local_path = subpath(path, old_root)
    return Path(root, local_path)


def is_ext(full_path:Path, ext:str) -> bool:
    return full_path.suffix.lower() == ext


def get_ext(path:Path):
    return path.suffix.lower()


class FileHandler:
    def handle_file(self, path:Path, local_path:str):
        # NO-OP
        pass

class NoOpHandler(FileHandler):
    pass

class CopyHandler(FileHandler):
    def __init__(self, target:Path):
        self.target = target

    def handle_file(self, path:Path, local_path:str):
        target_path = Path(self.target, local_path, path.name)
        log.debug(f"Copying {path} ||| {local_path} to {target_path}")
        path.copy(target_path)


class FileDispatcher:
    def __init__(self):
        self.handlers: dict[str,FileHandler] = {}
        self.defaultHandler = None


    def register(self, ext:str, handler:FileHandler):
        self.handlers[ext] = handler


    def setDefaultHandler(self, handler:FileHandler):
        self.defaultHandler = handler


    def walk(self, path:Path):
        if path.is_file():
            self.dispatch(path, local_path=None)
        else:
            # path is a directory, do a full walk
            for root, dirs, files in os.walk(path):
                local_path = subpath(root, path)
                for file in files:
                    file_path = Path(root, file)
                    self.dispatch(file_path, local_path)


    def dispatch(self, source:Path, local_path:str):
        ext = get_ext(source)
        handler = self.handlers.get(ext, self.defaultHandler)
        if handler:
            handler.handle_file(source, local_path)
        else:
            log.debug(f"Cannot dispatch, no handler for {ext}: {source}")
