import os
import logging
from pathlib import Path

from .page import Page

log = logging.getLogger(__name__)

class Converter:
    root: Path # Root for file walk, and to resolve rol paths


    def convert(self, infile:Path, outroot:Path) -> Page:
        raise NotImplementedError


    def convert_file(self, full_path:Path, outroot:str):
        ext = full_path.suffix.lower() # TODO strip first char, '.'

        # TODO: generic mapping to queue based on ext.
        if ext == ".docx":
            #docx_queue.append(full_path) # TODO async!
            page = self.convert(full_path, outroot)
            page.write(outroot)
        else:
            log.debug(f"No processor for {ext}, skipping {full_path}")


    def convert_directory(self, inpath:str, outroot:str):
        # load queues
        #docx_queue: list[Path] = []

        self.root = Path(inpath)

        if os.path.isfile(inpath):
            return self.convert_file(Path(inpath), outroot)

        for root, dirs, files in os.walk(self.root):
            for file in files:
                full_path = Path(root, file)
                self.convert_file(full_path, outroot)