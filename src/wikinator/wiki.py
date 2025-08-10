import os
import logging
from pathlib import Path

from dotenv import load_dotenv

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportQueryError

from .page import Page
from .converter import Converter
from .docxit import DocxitConverter


log = logging.getLogger(__name__)


class GraphDB:
    def __init__(self):
        self.client = self._init_client()
        self.pageCache = self.all_pages()

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


    def id_for_path(self, path:str) -> int:
        cached = self.pageCache.get(path)
        if cached:
            return cached["id"]
        else:
            return 0
        # query = gql(
        #     '''
        #     {
        #         pages {
        #             singleByPath(path:"$path", locale:"en") {
        #                 id
        #                 path
        #             }
        #         }
        #     }
        #     '''
        # )
        # try:
        #     result = self.client.execute(query, variable_values={"path":path})
        #     log.info(result)
        #     # if valid
        #     return result['id']
        # except TransportQueryError:
        #     log.debug(f"Path not found: {path}, ")
        #     return 0
        # except Exception as e:
        #     log.error(type(e).__name__)
        #     return 0


    def delete(self, page:Page) -> Page:
        id = self.id_for_path(page.path)
        if id > 0:
            log.info("TODO deleting page", page)


    def update(self, page:Page) -> Page:
        id = self.id_for_path(page.path)
        log.debug(f"Found id={id} for {page.path}")
        if id > 0:
            log.info(f"updating page {page.path}")
            page.id = id
            query = gql('''
                mutation Page (
                        $id: Int!,
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
                        update (
                            id:$id,
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
                ''')
            try:
                return self.client.execute(query, variable_values=vars(page))
            except TransportQueryError as e:
                log.error(f"update failed on {page.path}: {e}")
        else:
            # page doesn't exist! create!
            log.info(f"page doesn't exist, creating: {page.path}")
            return self.create(page)


    def create(self, page:Page) -> Page | None:
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
        response = self.client.execute(query, variable_values=vars(page))

        log.warning(response)

        result = response["pages"]["create"]["responseResult"]
        if not result["succeeded"]:
            log.error(f"Creation of {page.path} failed: {result["message"]}")
            return None

        return Page.load_json(response["pages"]["create"]["page"])

        # {"data":{"pages":{"create":{
        # "responseResult":{
        #   "succeeded":false,
        #   "errorCode":6002,
        #   "slug":"PageDuplicateCreate",
        #   "message":"Cannot create this page because an entry already exists at the same path."},
        # "page":null}}}}


    def all_pages(self):
        pages = {}

        # returns a map indexed by path
        query = gql(
            '''
            {
                pages {
                    list (orderBy: PATH, limit:5000) {
                    id
                    path
                    title
                    }
                }
            }
            '''
        )
        result = self.client.execute(query)

        for page in result["pages"]["list"]:
            pages[page["path"]] = page

        #log.info(pages)

        return pages


class GraphIngester(Converter):
    def __init__(self, output:bool = False):
        self.db = GraphDB()
        self.output = output

    # use the "file walk" from the converter to upload
    def convert_file(self, full_path:Path, outroot:str):
        wikipath = f"{outroot}/{full_path.parent}/{full_path.stem}"
        log.info(f"Converting {full_path} into {wikipath}")

        page = DocxitConverter.load_file(full_path)
        # make sure the path is correct
        page.path = wikipath

        self.db.update(page)

        if self.output:
            page.write(outroot)
