import os.path
import logging
import json
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

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


def extract_file_id_from_url(url: str) -> str:
    """Extract file ID from Google Drive URL."""
    if not url:
        return None
    
    # Handle different Google Drive URL formats
    if 'drive.google.com' in url:
        # Extract from URL parameters
        parsed = urlparse(url)
        if parsed.query:
            params = parse_qs(parsed.query)
            if 'id' in params:
                return params['id'][0]
        
        # Extract from path
        path_parts = parsed.path.split('/')
        for i, part in enumerate(path_parts):
            if part in ['file', 'folders'] and i + 1 < len(path_parts):
                file_id = path_parts[i + 1]
                # Validate that it looks like a Google Drive file ID
                if len(file_id) >= 25 and file_id.isalnum():
                    return file_id
    
    # If it's already just an ID
    if len(url) == 44 and url.isalnum():
        return url
    
    return None


def get_file_path(service, file_id: str) -> str:
    """Build file path by traversing parent folders."""
    try:
        path_parts = []
        current_id = file_id
        
        while current_id:
            file_metadata = service.files().get(
                fileId=current_id, 
                fields="name,parents"
            ).execute()
            
            path_parts.insert(0, file_metadata['name'])
            
            parents = file_metadata.get('parents', [])
            if parents:
                current_id = parents[0]
            else:
                current_id = None
        
        return '/'.join(path_parts)
    except HttpError as error:
        log.error(f"Error getting file path for {file_id}: {error}")
        return None


def fix_encoding_issues(content: str) -> str:
    """Fix common encoding issues in Google Docs content."""
    if not content:
        return content
    
    # Replace literal \n with actual newlines
    content = content.replace('\\n', '\n')
    
    # Fix other common encoding issues
    content = content.replace('\\t', '\t')
    content = content.replace('\\r', '\r')
    
    # Remove excessive whitespace
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    return content


def get_page(service, item) -> Page:
    """Download and convert a Google Doc to a Page object."""
    try:
        # Download content
        content = service.files().export(
            fileId=item['id'], 
            mimeType="text/markdown"
        ).execute()
        
        # Fix encoding issues
        content_str = fix_encoding_issues(str(content, 'utf-8'))
        
        # Get proper file path
        file_path = get_file_path(service, item['id'])
        if not file_path:
            file_path = item['name']  # Fallback to just the name
        
        return Page(
            title=item['name'],
            path=file_path,
            content=content_str,
            editor="markdown",
            locale="en",
            tags=None,
            description=f"generated from google docs id={item['id']}",
            isPublished=False,
            isPrivate=True,
        )
    except HttpError as error:
        log.error(f"Error downloading file {item['id']}: {error}")
        return None


def known_files(url: str = None) -> list[Page]:
    """Iterate over Google Docs files, generating pages with contents."""
    pages = []
    mimeType = 'application/vnd.google-apps.document'

    try:
        service = get_service()
        log.info("Connected to Google Drive API")
        
        # If URL is provided, extract file ID and get specific file
        if url:
            file_id = extract_file_id_from_url(url)
            if file_id:
                try:
                    file_metadata = service.files().get(
                        fileId=file_id,
                        fields="id,name,mimeType"
                    ).execute()
                    
                    if file_metadata['mimeType'] == mimeType:
                        page = get_page(service, file_metadata)
                        if page:
                            pages.append(page)
                    else:
                        log.warning(f"File {file_id} is not a Google Doc")
                except HttpError as error:
                    log.error(f"Error accessing file {file_id}: {error}")
            else:
                log.error(f"Could not extract file ID from URL: {url}")
        else:
            # List all Google Docs files
            request = service.files().list(
                pageSize=100,
                fields="nextPageToken, files(id,name,mimeType)",
                q=f"mimeType='{mimeType}'"
            )
            
            while request is not None:
                results = request.execute()
                items = results.get("files", [])
                
                if not items:
                    log.info("No Google Docs files found.")
                    break
                
                for item in items:
                    log.info(f"Processing: {item['name']} ({item['id']})")
                    page = get_page(service, item)
                    if page:
                        pages.append(page)
                
                request = service.files().list_next(request, results)

    except HttpError as error:
        log.error(f"Google Drive API error: {error}")
    except Exception as error:
        log.error(f"Unexpected error: {error}")

    return pages


def download_single_file(file_id: str) -> Page:
    """Download a single Google Doc by file ID."""
    try:
        service = get_service()
        file_metadata = service.files().get(
            fileId=file_id,
            fields="id,name,mimeType"
        ).execute()
        
        if file_metadata['mimeType'] == 'application/vnd.google-apps.document':
            return get_page(service, file_metadata)
        else:
            log.error(f"File {file_id} is not a Google Doc")
            return None
    except HttpError as error:
        log.error(f"Error downloading file {file_id}: {error}")
        return None









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
