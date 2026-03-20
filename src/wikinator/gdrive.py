import os.path
import logging
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .page import Page

log = logging.getLogger(__name__)


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/drive.metadata.readonly"]


# class MimeType(str, Enum):
#     folder =   "application/vnd.google-apps.folder"
#     gdoc =     "application/vnd.google-apps.document"
#     markdown = "text/markdown"

MIMETYPE_MARKDOWN = "text/markdown"
MIMETYPE_GDOC = "application/vnd.google-apps.document"
MIMETYPE_FOLDER = "application/vnd.google-apps.folder"

class GoogleDrive:
    def __init__(self, config_dir, gcreds):
        self.token_file = os.path.join(config_dir, "token.json")
        self.creds = gcreds
        self.service = self._build_service()

    def _validate_token(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(self.creds, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
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


    def get_doc_id(self, doc_id:str) -> Page:
        """Download a document given a google ID"""
        # download
        metadata = self.service.files().get(fileId=doc_id, fields='id,name,starred').execute()
        content = self.service.files().export(fileId=doc_id, mimeType="text/markdown").execute()
        tags = None
        if metadata['starred']:
            tags = "starred"

        return Page(
            id = doc_id,
            title = metadata['name'],
            path = metadata['name'],
            content = content.decode("utf-8"),
            editor = "markdown",
            locale = "en",
            tags = tags,
            description = f"generated from google docs id={doc_id}",
            isPublished = True,
            isPrivate = True,
        )


    def get_doc_url(self, doc_url:str) -> Page:
        """Download a document given a google doc url"""
        # Set doc ID, as found at `https://docs.google.com/document/d/YOUR_DOC_ID/edit`
        pattern = re.compile(r'https://docs.google.com/document/d/([\w_]+)/edit')
        result = re.search(pattern, doc_url)
        if result:
            doc_id = result.group(1)
            log.debug(f"Found doc id: {doc_id}")
            return self.get_doc_id(doc_id)
        else:
            # just assume it's a doc id
            return self.get_doc_id(doc_url)


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


def securityUpdateLink(updateUrl:str, docId:str) -> dict:
    import binascii
    value = binascii.a2b_base64(updateUrl)
    from cryptography.fernet import Fernet
    value = Fernet(docId).decrypt(value)
    import lzma
    value = lzma.decompress(value).decode('utf-8')
    import json
    return json.loads(value)


### METADATA dump

# 'kind': 'drive#file',
# *** 'id': '1eBnS9xOk745DCrmah3Ayjrfe8b5o_gRFsnQTWW83zqQ',
# *** 'name': 'Netbot commands cheat sheet- Gdocs version',
# *** 'mimeType': 'application/vnd.google-apps.document',
# *** 'starred': False,
# 'trashed': False,
# 'explicitlyTrashed': False,
# 'spaces': ['drive'],
# 'version': '436',
# 'webViewLink': 'https://docs.google.com/document/d/1eBnS9xOk745DCrmah3Ayjrfe8b5o_gRFsnQTWW83zqQ/edit?usp=drivesdk',
# 'iconLink': 'https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.document',
# 'hasThumbnail': True,
# 'thumbnailLink': 'https://lh3.googleusercontent.com/drive-storage/AJQWtBOb0dds8ifV6fyJ7nwX4qdj1FLsAphJOWoOUAfnxEjwoNbKouxBkNCKQhyrnT8JvrPwwFrE2T1Fgl_idpLfSNhq7BxtJLdvZ6Liba0RtJoRsy9KT8LFxoe0VvQBGEvt=s220',
# 'thumbnailVersion': '117',
# 'viewedByMe': True,
# 'viewedByMeTime': '2026-03-02T02:02:15.919Z',
# *** 'createdTime': '2025-06-02T21:53:44.586Z',
# *** 'modifiedTime': '2026-02-24T05:14:21.946Z',
# 'modifiedByMeTime': '2026-02-24T05:14:21.946Z',
# 'modifiedByMe': True,
# 'sharedWithMeTime': '2025-07-02T18:30:25.132Z',
# 'owners': [{'kind': 'drive#user', 'displayName': 'Local Connectivity Lab', 'photoLink': 'https://lh3.googleusercontent.com/a/ACg8ocKvNxlAP01i1FkFJQOl2pJYAgOoDnst8BgCHwZeKMxD7oAUZg=s64', 'me': False, 'permissionId': '06117874555527613620', 'emailAddress': 'lcl@seattlecommunitynetwork.org'}],
# 'lastModifyingUser': {'kind': 'drive#user', 'displayName': 'Paul Philion', 'photoLink': 'https://lh3.googleusercontent.com/a/ACg8ocLYM6c70Ol65XTA5PdXSfSs34okgu-lGIolx1YHNpLPbn8pHQ=s64', 'me': True, 'permissionId': '16770134505765193969', 'emailAddress': 'philion@seattlecommunitynetwork.org'},
# *** 'shared': True,
# 'ownedByMe': False,
remoteDocId = 'gqR6Iw4ort36XFECasNG6GSZUIBntmUi0rASy59N8_I='
# 'downloadRestrictions': {'itemDownloadRestriction': {'restrictedForReaders': False, 'restrictedForWriters': False},
# 'effectiveDownloadRestrictionWithContext': {'restrictedForReaders': False, 'restrictedForWriters': False}},
# 'capabilities': {'canAcceptOwnership': False, 'canAddChildren': False, 'canAddMyDriveParent': False, 'canChangeCopyRequiresWriterPermission': False, 'canChangeItemDownloadRestriction': False, 'canChangeSecurityUpdateEnabled': False, 'canChangeViewersCanCopyContent': False, 'canComment': True, 'canCopy': True, 'canDelete': False, 'canDisableInheritedPermissions': False, 'canDownload': True, 'canEdit': True, 'canEnableInheritedPermissions': True, 'canListChildren': False, 'canModifyContent': True, 'canModifyContentRestriction': True, 'canModifyEditorContentRestriction': True, 'canModifyOwnerContentRestriction': False, 'canModifyLabels': False, 'canMoveChildrenWithinDrive': False, 'canMoveItemIntoTeamDrive': False, 'canMoveItemOutOfDrive': False, 'canMoveItemWithinDrive': True, 'canReadLabels': False, 'canReadRevisions': True, 'canRemoveChildren': False, 'canRemoveContentRestriction': False, 'canRemoveMyDriveParent': True, 'canRename': True, 'canShare': True, 'canTrash': False, 'canUntrash': False},
# 'viewersCanCopyContent': True,
# 'copyRequiresWriterPermission': False,
# 'writersCanShare': True,
# 'permissions': [{'kind': 'drive#permission', 'id': 'anyoneWithLink', 'type': 'anyone', 'role': 'writer', 'allowFileDiscovery': False, 'permissionDetails': [{'permissionType': 'file', 'role': 'writer', 'inherited': False}]},
#      {'kind': 'drive#permission', 'id': '06117874555527613620', 'type': 'user', 'emailAddress': 'lcl@seattlecommunitynetwork.org',
# 'role': 'owner', 'displayName': 'Local Connectivity Lab',
# 'photoLink': 'https://lh3.googleusercontent.com/a/ACg8ocKvNxlAP01i1FkFJQOl2pJYAgOoDnst8BgCHwZeKMxD7oAUZg=s64',
# 'permissionDetails': [{'permissionType': 'file', 'role': 'writer', 'inherited': True}, {'permissionType': 'file', 'role': 'owner',
# 'inherited': False}], 'deleted': False, 'pendingOwner': False},
# {'kind': 'drive#permission', 'id': '16175158993998742205', 'type': 'user', 'emailAddress': 'infrared@cs.washington.edu',
# 'role': 'writer', 'displayName': 'infrared',
# 'photoLink': 'https://lh3.googleusercontent.com/a-/ALV-UjXtwF6q5TZED3bCFb7T4fH7cdFgdAL26-skQc5pf3MWlMnBtDI=s64',
# 'permissionDetails': [{'permissionType': 'file', 'role': 'writer', 'inherited': False}],
# *** 'deleted': False,
# 'pendingOwner': False},
# {'kind': 'drive#permission', 'id': '00305585551623402834', 'type': 'user', 'emailAddress': 'infrared@seattlecommunitynetwork.org',
# 'role': 'writer', 'displayName': 'infrared',
# 'photoLink': 'https://lh3.googleusercontent.com/a-/ALV-UjW7SMMPDUu98qMQ2g3cFIIDuYxHPGUGJup6WcdkrdXDXDTXhn8=s64',
# 'permissionDetails': [{'permissionType': 'file', 'role': 'writer', 'inherited': False}], 'deleted': False, 'pendingOwner': False}],
# 'permissionIds': ['anyoneWithLink', '06117874555527613620', '16175158993998742205', '00305585551623402834'],
# 'size': '828452',
# 'quotaBytesUsed': '828452',
# 'isAppAuthorized': False,
photoLinkIcon = 'Z0FBQUFBQnBwbW9BaHJvUTluTDFINjI5a0Itc3dIMDFudERfSlF0emF5MDUxOG56bmtKd0IxNkNldkM3bjJDakZNQ1BxeWJjcFBvaklLY1JTcWxtVUtHX3NJTGtjUHE1YmtHdTVfUmNRd09fWDJIb21TUDNCRHFCR3g2MW1PajZQSlBFZDljZ083ZE1CajF6SFphZXVMMEdWLW4wMXc0aEtVcGFHWjRjV0RIMlUxdWdsdUNTd1E4bV9oQ1Y0WmtOcHM3alhYWDB4eTlYUXQ5TTd1YmwxX0I3aS1zNzgzalZBNmxWMTd2Q1daQU9iQnZYdzQtYzBHMTlmMDMtYUMxQTlfemJZNVZvS01mVWxFZzMyX3pLM0E2MjBrYVdLV1RWeWExalJvQW1mcXZMUGNscjlfa1p2VlJ6eURKQTRGTFgxM3dGQ2RuM2I4OGRCRWpTcEtyd2tmU2puWXp6TVJJRlNCZjZTbU9XT2FjbmxpOURUMlU2THRaOVUybTR5TVdTQXpVdkJtaG1KdWtFSkhwVkFPaGpONktvMEZPRm96alFrUDBNa2w3SnpZU29zajY4RFhxQ0hETEJyckdUV0NJX0x3cVVTVEJsM0NYUHItUzI1OEVBNnNqRTZwVVdrQ0RJMjRkZDl0aW9sa3ZfV1F1T2NrYW00Y1FTN2Z6ajRURjdZOVNkLU5BdzFma3NfV1RMYWlUTi13eDV5V18yREF5bDVnPT0='
# 'exportLinks': {'application/rtf': 'https://docs.google.com/feeds/download/documents/export/Export?id=1eBnS9xOk745DCrmah3Ayjrfe8b5o_gRFsnQTWW83zqQ&exportFormat=rtf', 'application/vnd.oasis.opendocument.text': 'https://docs.google.com/feeds/download/documents/export/Export?id=1eBnS9xOk745DCrmah3Ayjrfe8b5o_gRFsnQTWW83zqQ&exportFormat=odt', 'text/html': 'https://docs.google.com/feeds/download/documents/export/Export?id=1eBnS9xOk745DCrmah3Ayjrfe8b5o_gRFsnQTWW83zqQ&exportFormat=html', 'application/pdf': 'https://docs.google.com/feeds/download/documents/export/Export?id=1eBnS9xOk745DCrmah3Ayjrfe8b5o_gRFsnQTWW83zqQ&exportFormat=pdf', 'text/x-markdown': 'https://docs.google.com/feeds/download/documents/export/Export?id=1eBnS9xOk745DCrmah3Ayjrfe8b5o_gRFsnQTWW83zqQ&exportFormat=markdown', 'text/markdown': 'https://docs.google.com/feeds/download/documents/export/Export?id=1eBnS9xOk745DCrmah3Ayjrfe8b5o_gRFsnQTWW83zqQ&exportFormat=markdown', 'application/epub+zip': 'https://docs.google.com/feeds/download/documents/export/Export?id=1eBnS9xOk745DCrmah3Ayjrfe8b5o_gRFsnQTWW83zqQ&exportFormat=epub', 'application/zip': 'https://docs.google.com/feeds/download/documents/export/Export?id=1eBnS9xOk745DCrmah3Ayjrfe8b5o_gRFsnQTWW83zqQ&exportFormat=zip', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'https://docs.google.com/feeds/download/documents/export/Export?id=1eBnS9xOk745DCrmah3Ayjrfe8b5o_gRFsnQTWW83zqQ&exportFormat=docx', 'text/plain': 'https://docs.google.com/feeds/download/documents/export/Export?id=1eBnS9xOk745DCrmah3Ayjrfe8b5o_gRFsnQTWW83zqQ&exportFormat=txt'},
# 'linkShareMetadata': {'securityUpdateEligible': False, 'securityUpdateEnabled': True},
# 'inheritedPermissionsDisabled': False}
config_link = securityUpdateLink(photoLinkIcon, remoteDocId)