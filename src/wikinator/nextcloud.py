
import logging
from pathlib import Path

from wikinator.dispatcher import FileHandler

log = logging.getLogger(__name__)

class NextCloudHandler(FileHandler):
    def __init__(self, target:Path):
        super().__init__()
        # load nextcloud info from config, or fail
        self.target = target

    def handle_file(self, path:Path, local_path:str):
        # TODO: Use webDAV to upload files to nextcloud, based on provided settings
        #log.info(f"ASPIRATIONAL: Uploading file to nextcloud: {path} -> {local_path}")
        pass