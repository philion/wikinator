import os.path
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .page import Page

log = logging.getLogger(__name__)


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/drive.metadata.readonly"]
# https://www.googleapis.com/auth/drive.readonly
# https://www.googleapis.com/auth/drive.metadata.readonly


# class MimeType(str, Enum):
#     folder =   "application/vnd.google-apps.folder"
#     gdoc =     "application/vnd.google-apps.document"
#     markdown = "text/markdown"

MIMETYPE_MARKDOWN = "text/markdown"
MIMETYPE_GDOC = "application/vnd.google-apps.document"
MIMETYPE_FOLDER = "application/vnd.google-apps.folder"


# def validate_token():
#     # The file token.json stores the user's access and refresh tokens, and is
#     # created automatically when the authorization flow completes for the first
#     # time.
#     # FIXME store token and creds in user home `.config/wikinator`
#     creds = None
#     if os.path.exists("token.json"):
#         creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#     # If there are no (valid) credentials available, let the user log in.
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 "credentials.json", SCOPES
#             )
#             creds = flow.run_local_server(port=0)
#         # Save the credentials for the next run
#         with open("token.json", "w") as token:
#             token.write(creds.to_json())
#     return creds


# def get_service():
#     creds = validate_token()
#     service = build("drive", "v3", credentials=creds)
#     return service


# def get_page(service, item) -> Page:
#     #print(item.keys())
#     #print(json.dumps(item, indent=4))

#     # download
#     content = service.files().export(fileId=item['id'], mimeType=MimeType.markdown).execute()
#     return Page(
#         title = item['name'],
#         path = item['name'], #item.get('parents', "-"), # FIXME
#         content = str(content),
#         editor = "markdown",
#         locale = "en",
#         tags = None,
#         description = f"generated from google docs id={item['id']}",
#         isPublished = False,
#         isPrivate = True,
#     )



# def known_files(id:str) -> list[Page]:
#     """
#     id can be '/', to start at the root,
#     or the ID of a folder or a file
#     """
#     # iterate over the known files,
#     # generating a page with the contents of each

#     pages = []

#     try:
#         service = get_service()
#         #request = service.files().list(pageSize=20, fields=f"nextPageToken, files(mimeType='${MimeType.gdoc}')")
#         request = service.files().list(pageSize=20, fields="nextPageToken, files(*)")
#         #request = service.files().list(q="mimeType='${MimeType.gdoc}'")
#         while request is not None:
#             results = request.execute()

#             items = results.get("files", [])
#             print("items found:", len(items))
#             if not items:
#                 log.debug("No files found.")
#                 return
#             for item in items:
#                 #print(json.dumps(item, indent=4))
#                 print(item['id'], item['name'], item['mimeType'])

#                 if item['mimeType'] == MimeType.gdoc:
#                     # download
#                     page = get_page(service, item)
#                     pages.append(page)
#                 else:
#                     print('.', end='')
#                     #print("skipping", item['name'], item['mimeType'])

#             request = service.files().list_next(request, results)

#     except HttpError as error:
#         # TODO(developer) - Handle errors from drive API.
#         print(f"An error occurred: {error}")

#     return pages


class GoogleDrive:

    def __init__(self):
        self.service = self._build_service()

    def _validate_token(self):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        # FIXME store token and creds in user home `.config/wikinator`
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return creds


    def _build_service(self):
        creds = self._validate_token()
        service = build("drive", "v3", credentials=creds)
        return service


    def get_parents(self, id) -> str:
        if id is None:
            return None

        try:
            file = self.service.files().get(fileId=id, fields="id,name,parents").execute()
            # TODO check results
            name = file['name']
            parent_id = file.get("parents", [None])[0]
            parent_name = self.get_parents(parent_id) # recusrion!
            return parent_name + "/" +  name if parent_name else name
        except Exception as ex:
            log.error(f"Error getting id={id}: {ex}")
            return None


        # #print(json.dumps(file, indent=4))
        # #print(">>> KIND:", file['kind'])

        # if file['kind'] == "drive#folder":
        #     #print("FOLDER", file['name'])
        #     name = file['name']
        #     parent_id = file.get("parents", [None])[0]
        #     return self.get_parents(parent_id) / name
        # elif file['kind'] == "drive#file":
        #     print("FILE", file['name'], file['mimeType'])
        #     parent_id = file.get("parents", [None])[0]
        #     self.get_parents(parent_id) / name
        # else:
        #     print("Unknown file type:", file['kind'])
        #     return file['name']

        # if there are parents, return metadata
        # should end with a list ["top", "middle", "end"] for "/top/middle/end"


    def get_page(self, item) -> Page:
        # FIXME log.info()
        print(f"getting page for {item['name']}")
        path = self.get_parents(item['id'])

        # download
        content = self.service.files().export(fileId=item['id'], mimeType="text/markdown").execute()
        return Page(
            title = item['name'],
            path = path,
            content = content.decode("utf-8"),
            editor = "markdown",
            locale = "en",
            tags = None,
            description = f"generated from google docs id={item['id']}",
            isPublished = False,
            isPrivate = True,
        )


    # def gather_files(self, id):
    #     if id == "/": #query from root
    #         request = self.service.files().list()
    #     else:
    #         query =
    #         request = self.service.files().list()

    #     while request is not None:
    #         results = request.execute()

    #         items = results.get("files", [])
    #         if not items:
    #             log.debug("No files found.")
    #             return
    #         for item in items:
    #             #print(json.dumps(item, indent=4))
    #             #print(item['id'], item['name'], item['mimeType'])

    #             if item['mimeType'] == MimeType.gdoc:
    #                 # download
    #                 page = get_page(service, item)
    #                 pages.append(page)
    #             else:
    #                 print('.', end='')
    #                 #print("skipping", item['name'], item['mimeType'])

    #         request = service.files().list_next(request, results)


    def get_item(self, id:str):
        return self.service.files().get(fileId=id).execute()

    def get_children(self, id:str) -> list:
        kids = []
        # FIXME
        # query = f"'{id}' in parents"
        # response = self.service.files().list(q=query).execute()
        # files.append(response.get('files'))
        # nextPage = response.get("nextPageToken")
        # while nextPage:
        #     response = self.service.files().list(q=query).execute()
        #     files.append(response.get('files'))
        #     nextPage = response.get("nextPageToken")
        return kids


    def list_files(self, mimeType:str) -> list[Page]:
        """
        produce a list a file IDs that match the give file
        type
        """
        pages = []

        query = f"mimeType = '{mimeType}'"
        request = self.service.files().list(pageSize=10, q=query, fields="*")
        while request is not None:
            results = request.execute()
            items = results.get("files", [])
            for item in items:
                #print(json.dumps(item, indent=4))
                #path = self.get_parents(id)
                page = self.get_page(item)
                #print(page.path)
                pages.append(page)
            request = self.service.files().list_next(request, results)

        return pages


    def known_files(self, id:str) -> list[str]:
        """
        id can be '/', to start at the root,
        or the ID of a folder or a file

        """
        # iterate over the known files,
        # generating a page with the contents of each

        pages = []
        #mimeType = MimeType.gdoc

        try:
            #service = get_service()
            #print("got service:", service)
            #files = service.files()
            #print("---", files, type(files))
            # IF url, strip out ID
            #file = service.files().get(fileId=url).execute()
            #print("->>", file)

            #request = service.files().list(pageSize=20, fields=f"nextPageToken, files(mimeType='${MimeType.gdoc}')")
            #request = self.service.files().list(pageSize=20, fields="nextPageToken, files(*)")
            #request = self.service.files().list(q="mimeType='${MimeType.gdoc}'")
            request = self.service.files().list(pageSize=100, q=f"mimeType = '{MIMETYPE_FOLDER}'")



            while request is not None:
                results = request.execute()

                items = results.get("files", [])
                if not items:
                    log.debug("No files found.")
                    return
                for item in items:
                    #print(json.dumps(item, indent=4))
                    #print(item['id'], item['name'], item['mimeType'])

                    if item['mimeType'] == MIMETYPE_GDOC:
                        # download
                        #page = self.get_page(item)
                        pages.append(item)
                    elif item['mimeType'] == MIMETYPE_FOLDER:
                        print("TODO - download folder, name:", item['name'], ", id:", item['name'])
                        pages.extend()
                    elif item['mimeType'].startswith("image/") or item['mimeType'].startswith("video/"):
                        print(".", end="")
                    else:
                        #print('.', end='')
                        print("skipping", item['name'], item['mimeType'])

                request = self.service.files().list_next(request, results)

        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f"An error occurred: {error}")

        return pages





# def main():
#     """Shows basic usage of the Drive v3 API.
#     Prints the names and ids of the first 10 files the user has access to.
#     """
#     creds = None
#     # The file token.json stores the user's access and refresh tokens, and is
#     # created automatically when the authorization flow completes for the first
#     # time.
#     if os.path.exists("token.json"):
#         creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#     # If there are no (valid) credentials available, let the user log in.
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 "credentials.json", SCOPES
#             )
#             creds = flow.run_local_server(port=0)
#         # Save the credentials for the next run
#         with open("token.json", "w") as token:
#             token.write(creds.to_json())

#     try:
#         service = build("drive", "v3", credentials=creds)

#         # Call the Drive v3 API
#         files = service.files()
#         request = files.list(pageSize=1, fields="nextPageToken, files(*)")

#         #while request is not None:
#         results = request.execute()

#         items = results.get("files", [])
#         if not items:
#             print("No files found.")
#             return
#         for item in items:
#             #print(json.dumps(item, indent=4))
#             print(item['name'], item['mimeType'])

#             # download
#             md_doc = files.export(fileId=item['id'], mimeType="text/markdown").execute()
#             print(md_doc)

#         #    request = files.list_next(request, results)

#     except HttpError as error:
#         # TODO(developer) - Handle errors from drive API.
#         print(f"An error occurred: {error}")


# if __name__ == "__main__":
#     main()
