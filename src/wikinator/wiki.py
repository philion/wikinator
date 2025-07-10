import os
from pathlib import Path

from dotenv import load_dotenv

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from .page import Page
from .converter import Converter


class GraphDB:
    def __init__(self):
        self.client = self._init_client()

    def _init_client(self) -> Client:
        """
        Initialize the GraphQL client with the credentials found in the system ENV:
        - GRAPH_DB : The full URL for requests to the graph DB
        - AUTH_TOKEN : Security token to authorize session
        """
        load_dotenv()
        db_url = os.getenv("GRAPH_DB")
        token = os.getenv("AUTH_TOKEN")
        transport = AIOHTTPTransport(url=db_url, headers={'Authorization': f'Bearer {token}'}, ssl=True)
        return Client(transport=transport)

    def store(self, page:Page):
        query = gql(
            '''
            mutation Page (
                    $content: String!,
                    $description: String!,
                    $editor:String!,
                    $isPublished:Boolean!,
                    $isPrivate:Boolean!,
                    $locale:String!,
                    $path:String!,
                    $tags:[String]!,
                    $title:String!) {
                pages {
                    create (
                        content:$content,
                        description:$description,
                        editor: $editor,
                        isPublished: $isPublished,
                        isPrivate: $isPrivate,
                        locale: $locale,
                        path:$path,
                        tags: $tags,
                        title:$title
                    ) {
                        responseResult {
                            succeeded
                            errorCode
                            slug
                            message
                        }
                        page {
                            id
                            path
                            title
                        }
                    }
                }
            }
            '''
        )
        print('---', page.path)
        result = self.client.execute(query, variable_values=vars(page))
        print(result)
        return result


class GraphIngester(Converter):
    def __init__(self):
        self.db = GraphDB()

    # use the "file walk" from the converter to upload
    def convert_file(self, full_path:Path, outroot:str):
        page = Page.load_file(full_path)
        self.db.store(page)


# --- OLD --- migrating to client class

# def store_page(client: Client, params: dict):
#     # store in file?
#     query = gql(
#         '''
#         mutation Page (
#                 $content: String!,
#                 $description: String!,
#                 $editor:String!,
#                 $isPublished:Boolean!,
#                 $isPrivate:Boolean!,
#                 $locale:String!,
#                 $path:String!,
#                 $tags:[String]!,
#                 $title:String!) {
#             pages {
#                 create (
#                     content:$content,
#                     description:$description,
#                     editor: $editor,
#                     isPublished: $isPublished,
#                     isPrivate: $isPrivate,
#                     locale: $locale,
#                     path:$path,
#                     tags: $tags,
#                     title:$title
#                 ) {
#                     responseResult {
#                         succeeded
#                         errorCode
#                         slug
#                         message
#                     }
#                     page {
#                         id
#                         path
#                         title
#                     }
#                 }
#             }
#         }
#         '''
#     )
#     print('---', params['path'])
#     result = client.execute(query, variable_values=params)
#     print(result)
#     return result

# EXTS = {
#     ".docx":
#  32
# .pdf 87
# .xlsx 15
# .rsc 4
# .drawio 4
# .deb 8
# .bin 1
# .mp4 28
# .png 49
# .PDF 7
# .pptx 1
# .apk 10
# .jpg 5
# .HEIC 21
# .tgz 1
# .php 2
# .yaml 2
# .gz 1
# .toml 1
# .service 1
# .jpeg 2
# .txt 1
# .csv 1
# }

### Design Notes
# multiprocessing.JoinableQueue for queues, using both get() and task_done()

#running = False
#docx_queue = multiprocessing.JoinableQueue()

# def docx_worker(client: Client):
#     while running:
#         try:
#             item = docx_queue.get(timeout=0.01)
#             if item is None:
#                 continue

#             try:
#                 process_docx(client, item)
#             finally:
#                 docx_queue.task_done()

#         except queue.Empty:
#             pass
#         except:
#             logging.exception('error while processing item')

#CLIENT: Client = init_client()



#def main():
    #CLIENT = init_client()
    #process_directory("./data")

    # client = init_client()

    # with open("sample.adoc", 'r') as file:
    #     file_content = file.read()

    # params = {
    #     "title": "This is a test",
    #     "path": "test/test-43",
    #     "content": file_content,
    #     "editor": "asciidoc",
    #     "locale": "en",
    #     "tags": "",
    #     "description": "generated from googledoc/...",
    #     "isPublished": False,
    #     "isPrivate": True,
    # }

    # page = create_page(client, params)
    # print(json.dumps(page, indent=4))







### other queries. remove when stable
    # query = gql(
    #     """
    #     {
    #         pages {
    #             list (orderBy: TITLE) {
    #                 id
    #                 path
    #                 title
    #                 contentType
    #                 createdAt
    #                 description
    #                 isPrivate
    #                 isPublished
    #                 updatedAt
    #             }
    #         }
    #     }
    #     """
    # )

    # query = gql(
    #     """
    #     {
    #         users {
    #             list {
    #                 id
    #                name
    #                email
    #             }
    #         }
    #     }
    #     """
    # )

    # insert into "pages" (
        # "authorId",
        # "content",
        # "contentType",
        # "createdAt",
        # "creatorId",
        # "description",
        # "editorKey",
        # "extra",
        # "hash",
        # "isPrivate",
        # "isPublished",
        # "localeCode",
        # "path",
        # "publishEndDate",
        # "publishStartDate",
        # "title",
        # "toc",
        # "updatedAt")

    # query = gql(
    #     """
    #     mutation Page ($content: String!, $description: String!, $editor:String!, $isPublished:Boolean!, $isPrivate:Boolean!, $locale:String!, $path:String!,$tags:[String]!, $title:String!) {
    #         pages {
    #             create (content:$content, description:$description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path:$path, tags: $tags, title:$title) {
    #                 responseResult {
    #                     succeeded,
    #                     errorCode,
    #                     slug,
    #                     message
    #                 },
    #                 page {
    #                     id,
    #                     path,
    #                     title
    #                 }
    #             }
    #         }
    #     }
    #     """
    # )

    # query = gql(
    #     '''
    #     mutation Page (
    #             $content: String!,
    #             $description: String!,
    #             $editor:String!,
    #             $isPublished:Boolean!,
    #             $isPrivate:Boolean!,
    #             $locale:String!,
    #             $path:String!,
    #             $tags:[String]!,
    #             $title:String!) {
    #         pages {
    #             create (
    #                 content:$content,
    #                 description:$description,
    #                 editor: $editor,
    #                 isPublished: $isPublished,
    #                 isPrivate: $isPrivate,
    #                 locale: $locale,
    #                 path:$path,
    #                 tags: $tags,
    #                 title:$title
    #             ) {
    #                 responseResult {
    #                     succeeded
    #                     errorCode
    #                     slug
    #                     message
    #                 }
    #                 page {
    #                     id
    #                     path
    #                     title
    #                 }
    #             }
    #         }
    #     }
    #     '''
    # )

    # query = gql(
    #     """
    #     query getContinentName ($code: ID!) {
    #     continent (code: $code) {
    #         name
    #       }
    #     }
    # """
    # )
