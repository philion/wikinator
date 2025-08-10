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
        query = gql(
            '''
            {
                pages {
                    singleByPath(path:"$path", locale:"en") {
                        id
                        path
                    }
                }
            }
            '''
        )
        try:
            result = self.client.execute(query, variable_values={"path":path})
            log.info(result)
            # if valid
            return result['id']
        except TransportQueryError:
            log.debug(f"Path not found: {path}, ")
            return 0
        except Exception as e:
            log.error(type(e).__name__)
            return 0


    def delete(self, page:Page) -> Page:
        id = self.id_for_path(page.path)
        if id > 0:
            log.info("TODO deleting page", page)


    def update(self, page:Page) -> Page:
        id = self.id_for_path(page.path)
        if id > 0:
            log.info("updating page", page.path)
            query = gql('''
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
            return self.client.execute(query, variable_values=vars(page))
        else:
            # page doesn't exist! create!
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
        result = response["responseResult"]
        if not result["succeeded"]:
            log.error(f"Creation of {page.path} failed: {result["message"]}")
            return None

        page = Page.load_json(response["page"])

        # {"data":{"pages":{"create":{
        # "responseResult":{
        #   "succeeded":false,
        #   "errorCode":6002,
        #   "slug":"PageDuplicateCreate",
        #   "message":"Cannot create this page because an entry already exists at the same path."},
        # "page":null}}}}

        return page


class GraphIngester(Converter):
    def __init__(self):
        self.db = GraphDB()

    # use the "file walk" from the converter to upload
    def convert_file(self, full_path:Path, outroot:str):
        wikipath = f"{outroot}/{full_path.parent}/{full_path.stem}"
        log.info(f"Converting {full_path} into {wikipath}")

        page = DocxitConverter.load_file(full_path)
        # make sure the path is correct
        page.path = wikipath

        self.db.update(page)
