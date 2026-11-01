
import logging
from pathlib import Path

from wikinator.config import AppConfig
from wikinator.dispatcher import FileHandler
from wikinator.images import load_as

import nc_py_api


log = logging.getLogger(__name__)


class NextCloudClient:
    def __init__(self):
        config = AppConfig()
        #self.nc = nc_py_api.AsyncNextcloud(
        self.nc = nc_py_api.Nextcloud(
            nextcloud_url=config.get('nextcloud_url'),
            nc_auth_user=config.get('nextcloud_user'),
            nc_auth_pass=config.get('nextcloud_token'))


    def upload(self, local_file:Path, remote_path:Path):
        # make sure directory exists
        self.nc.files.makedirs(str(remote_path), exist_ok=True)

        with open(local_file, "rb") as file:
            data = file.read()

            # upload the file
            remote_file = remote_path / local_file.name
            print(f"Uploading {local_file} to {remote_file}....", end="")

            result = self.nc.files.upload(str(remote_file), data)
            print("done.")
            return result


    def convert_upload(self, local_file:Path, remote_path:Path):
        # make sure directory exists
        self.nc.files.makedirs(str(remote_path), exist_ok=True)

        # load and convert file into buffer
        format = "jpeg"
        quality = 85
        print(f"Converting {local_file} to {format}....", end="")
        buffer = load_as(local_file, format, quality)
        remote_file = remote_path / (local_file.stem + '.' + format)

        print(f"uploading to {remote_file}....", end="")
        result = self.nc.files.upload_stream(str(remote_file), buffer)
        print("done.")
        return result


_client = NextCloudClient()


class NextCloudHandler(FileHandler):
    def __init__(self, remote_root:str = ""):
        self.target = Path(remote_root)
        self.client = _client


    def handle_file(self, path:Path, remote_path:str):
        self.client.upload(path, self.target / remote_path)


class NextCloudImageConverter(FileHandler):
    def __init__(self, remote_root:str = ""):
        self.target = Path(remote_root)
        self.client = _client


    def handle_file(self, path:Path, remote_path:str):
        self.client.convert_upload(path, self.target / remote_path)


# # For testing the image stuff
# def main():
#     import sys
#     source = sys.argv[1]
#     path = Path(source)
#     rel_path = subpath(path, Path('~/Downloads').expanduser())
#     rel_path = Path(rel_path).parent

#     print(f"Converting {path} -> {rel_path}")

#     client = NextCloudClient()
#     #client.convert_upload(path, rel_path)
#     client.upload(path, rel_path)



# if __name__ == "__main__":
#     main()
