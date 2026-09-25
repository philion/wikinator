import os
import logging
from pathlib import Path
import zipfile

from .page import Page

log = logging.getLogger(__name__)

SUPPORTED_EXTS = { ".docx" }

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


    def convert_zip_file(self, inpath:Path, outroot:str):
        with zipfile.ZipFile(inpath, 'r') as myzip:
            for info in myzip.infolist():
                path = zipfile.Path(myzip, info.filename)
                ext = path.suffix.lower()
                if ext in SUPPORTED_EXTS:
                    #print(ext, path)
                    self.convert_file(path, outroot)


    def convert_local_files(self, inpath:str, outroot:str):
        # load queues
        #docx_queue: list[Path] = []

        self.root = Path(inpath)

        if os.path.isfile(inpath):
            if inpath.lower().endswith('.zip'):
                return self.convert_zip_file(Path(inpath), outroot)
            else:
                return self.convert_file(Path(inpath), outroot)

        for root, dirs, files in os.walk(self.root):
            for file in files:
                full_path = Path(root, file)
                self.convert_file(full_path, outroot)