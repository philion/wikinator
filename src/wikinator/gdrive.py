import os.path
import logging
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .page import Page

log = logging.getLogger(__name__)


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
# https://www.googleapis.com/auth/drive.readonly
# https://www.googleapis.com/auth/drive.metadata.readonly


def validate_token():
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


def get_service():
    creds = validate_token()
    service = build("drive", "v3", credentials=creds)
    return service


def get_page(service, item) -> Page:
    #print(item.keys())
    #print(json.dumps(item, indent=4))

    # download
    content = service.files().export(fileId=item['id'], mimeType="text/markdown").execute()
    return Page(
        title = item['name'],
        path = item['name'], #item.get('parents', "-"), # FIXME
        content = str(content),
        editor = "markdown",
        locale = "en",
        tags = None,
        description = f"generated from google docs id={item['id']}",
        isPublished = False,
        isPrivate = True,
    )

def known_files(url:str) -> list[Page]:
    # iterate over the known files,
    # generating a page with the contents of each

    pages = []
    mimeType = 'application/vnd.google-apps.document'

    try:
        service = get_service()
        print("got service:", service)
        #files = service.files()
        #print("---", files, type(files))
        # IF url, strip out ID
        #file = service.files().get(fileId=url).execute()
        #print("->>", file)

        #request = service.files().list(pageSize=20, fields=f"nextPageToken, files(mimeType='${mimeType}')")
        request = service.files().list(pageSize=20, fields="nextPageToken, files(*)")
        while request is not None:
            results = request.execute()

            items = results.get("files", [])
            if not items:
                log.debug("No files found.")
                return
            for item in items:
                #print(json.dumps(item, indent=4))
                #print(item['id'], item['name'], item['mimeType'])

                if item['mimeType'] == mimeType:
                    # download
                    page = get_page(service, item)
                    pages.append(page)
                else:
                    print('.', end='')
                    #print("skipping", item['name'], item['mimeType'])

            request = service.files().list_next(request, results)

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
