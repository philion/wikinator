import os
import logging
from pathlib import Path

from dotenv import load_dotenv

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

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
        wikipath = f"{outroot}/{full_path.parent}/{full_path.stem}"
        log.info(f"Converting {full_path} into {wikipath}")
        page = DocxitConverter.load_file(full_path)
        page.path = wikipath
        self.db.store(page)
