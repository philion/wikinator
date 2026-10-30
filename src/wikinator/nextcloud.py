
import logging
from pathlib import Path

from webdav3.client import Client

from wikinator.config import AppConfig
from wikinator.dispatcher import FileHandler
from wikinator.images import convert_to

log = logging.getLogger(__name__)

def _init_client() -> Client:
    config = AppConfig()
    options = {
        'webdav_hostname': config.get('nextcloud_url'),
        'webdav_login':    config.get('nextcloud_user'),
        'webdav_token':    config.get('nextcloud_token'),
    }
    # TODO: Validate config/options
    client = Client(options)
    # client.verify = False # To not check SSL certificates (Default = True)
    # client.session.proxies(...) # To set proxy directly into the session (Optional)
    # client.session.auth(...) # To set proxy auth directly into the session (Optional)
    # client.execute_request("mkdir", 'directory_name')
    return client

_webdav = _init_client()
assert _webdav is not None


class NextCloudHandler(FileHandler):
    def __init__(self):
        # load nextcloud info from config, or fail
        self.target = Path("/Documents")
        self.client = _webdav


    def handle_file(self, path:Path, subpath:str):
        remote_path = self.target / subpath / path.name
        #converted = convert_to(path)
        #self.client.upload_sync(remote_path=remote_path, local_path=converted)
        #converted.delete()
        print(">>> UPLOAD orig:", path, "remote:", remote_path)
        # LATER? link = self.client.publish("dir1/file1")


_image_dir = Path("/Photos")

class NextCloudImageHandler(FileHandler):
    def __init__(self):
        # load nextcloud info from config, or fail
        self.target = _image_dir
        self.client = _webdav


    def handle_file(self, path:Path, subpath:str):
        remote_path = self.target / subpath / (path.stem + '.jpeg')
        #converted = convert_to(path)
        #self.client.upload_sync(remote_path=remote_path, local_path=converted)
        #converted.delete()
        print(">>> CONVERT orig:", path, "remote:", remote_path)
        # LATER? link = self.client.publish("dir1/file1")


class NextCloudImageConverter(FileHandler):
    def __init__(self):
        self.target = _image_dir
        if _webdav:
            self.client = _webdav
        else:
            log.error("Unable to load nextcloud client")
        # load nextcloud info from config, or fail


    def handle_file(self, path:Path, subpath:str):
        remote_path = self.target / subpath / (path.stem + '.jpeg')
        #converted = convert_to(path)
        #self.client.upload_sync(remote_path=remote_path, local_path=converted)
        #converted.delete()
        print(">>> CONVERT orig:", path, "remote:", remote_path)
        # LATER? link = self.client.publish("dir1/file1")
