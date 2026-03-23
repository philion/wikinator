import io
import logging
from pathlib import Path

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportQueryError
import requests


from wikinator.config import AppConfig

from .page import Page
from .converter import Converter
from .docxit import DocxitConverter


log = logging.getLogger(__name__)


class GraphDB:
    def __init__(self, url:str, token:str):
        self.url = url
        self.token = token # FIXME: REMOVE - this is only used for testing file upload using other tools
        self.client = self._init_client(url, token)
        self.pageCache = self.all_pages()


    @classmethod
    def from_config(cls, config:AppConfig):
        url = config.get('db_url')
        token = config.get('db_token')
        return cls(url, token)


    def _init_client(self, url:str, token:str) -> Client:
        """
        Initialize the GraphQL client with the credentials found in the system ENV:
        - GRAPH_DB : The full URL for requests to the graph DB
        - AUTH_TOKEN : Security token to authorize session
        """
        transport = AIOHTTPTransport(url=url + '/graphql', headers={'Authorization': f'Bearer {token}'}, ssl=True)
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
        if page.tags is None:
            page.tags = ["gdocs"]

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
                # images:
                if page.images:
                    for rId in page.images:
                        self.upload_image(page, rId)

                return self.client.execute(query, variable_values=page.vars())
            except TransportQueryError as e:
                log.error(f"update failed on {page.path}: {e}")
        else:
            # page doesn't exist! create!
            log.info(f"page doesn't exist, creating: {page.path}")
            return self.create(page)


    def create(self, page:Page) -> Page | None:
        if page.tags is None:
            page.tags = ["gdocs"]

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
        try:
            # images:
            log.warning("Uploading images")
            if page.images:
                for rId in page.images:
                    log.warning(f"Uploading image {rId}")
                    self.upload_image(page, rId)

            log.warning(f"creating: {query}")
            response = self.client.execute(query, variable_values=page.vars())

            log.warning(f"CREATE: {response}")

            result = response["pages"]["create"]["responseResult"]
            if not result["succeeded"]:
                log.error(f"Creation of {page.path} failed: {result["message"]}")
                return None

            log.info(f"#### {response["pages"]["create"]["page"]}")
            result_page = Page.load(response["pages"]["create"]["page"])


            return result_page
        except Exception as ex:
            log.error(f"Error creating {page.path}: {ex}")
            return None

        # {"data":{"pages":{"create":{
        # "responseResult":{
        #   "succeeded":false,
        #   "errorCode":6002,
        #   "slug":"PageDuplicateCreate",
        #   "message":"Cannot create this page because an entry already exists at the same path."},
        # "page":null}}}}


    # # return the image path
    # def create_image(self, page:Page, rId:str) -> str:
    #     image = page.get_image(rId)
    #     path = page.get_image_path(rId) # this scopes the path with the page name and path
    #     # FIXME upload image.content

    #     query = gql('''
    #         mutation($file: Upload!) {
    #             singleUpload(file: $file) {
    #                 id
    #             }
    #         }
    #     ''')

    #     query.variable_values = {
    #         "file": FileVar(
    #             io.BytesIO(image.content),
    #             filename=path,
    #             content_type=mimetype_from_path(path),
    #         ),
    #     }

    #     response = self.client.execute(query, upload_files=True)
    #     log.debug(f"create_image: {path} --> {response}")
    #     # FIXME - process response

    #     return path


    # async def upload_asset(self, file_path: str, file_name: str, asset_folder_id: int):

    #     headers = {
    #         'Authorization': f"Bearer {self.token}",
    #     }
    #     async with aiohttp.ClientSession() as session:

    #         data = aiohttp.FormData(quote_fields=False)
    #         data.add_field('mediaUpload', f'{{"folderId":{asset_folder_id}}}')
    #         data.add_field('mediaUpload', open(file_path, 'rb'), filename=file_name,
    #                     content_type='image/jpeg')

    #         try:
    #             async with session.post(
    #                     url=self.url + "/u",
    #                     data=data,
    #                     headers=headers
    #             ) as resp:
    #                 log.info(f"status: {resp.status}")
    #                 result = await resp.text()
    #                 log.info(f"upload: {result}")
    #                 return result
    #         except aiohttp.ClientConnectorError and aiohttp.ServerTimeoutError:
    #             logging.exception("Exception in upload_asset")
    #             return {}


    def upload_image(self, page:Page, rId:str) -> str:
        image = page.get_image(rId)
        path = page.get_image_path(rId) # this scopes the path with the page name and path
        url = self.url + "/u"

        try:
            with io.BytesIO(image.content) as image_data:
                headers = {
                    'Authorization': f'Bearer {self.token}'
                }

                files = (
                    ('mediaUpload', (None, '{"folderId":0}')),  # Using root asset folder
                    ('mediaUpload', (path, image_data, image.mimetype))
                )

                log.debug(f"Sending upload request: {url} POST {image.name}/{image.mimetype} -> {path}")
                result = requests.post(url, headers=headers, files=files)
                if result.ok:
                    log.info(f"Upload OK: status={result.status_code} path={path}")
                else:
                    log.warning(f"Image upload failed: {page.title} {image.name}")
        except Exception:
            log.exception(f"Error uploading ${path}")


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
    def __init__(self, url:str, token:str, output:bool = False):
        self.db = GraphDB(url, token)
        self.output = output

    # use the "file walk" from the converter to upload
    def convert_file(self, full_path:Path, outroot:str):
        # FIXME: file/path naming should be abstracted somehow.
        if outroot.strip() in ["/", ""]:
            outroot = ""
            wikipath = f"{full_path.parent}/{full_path.stem}"
        else:
            wikipath = f"{outroot}/{full_path.parent}/{full_path.stem}"

        # replace chars in path
        log.info(f"BEFORE {wikipath}")

        wikipath = wikipath.replace(" ", "_")
        wikipath = wikipath.replace(".", "_")
        log.info(f"Converting {full_path} into {wikipath}")

        page = DocxitConverter.load_file(full_path)
        if page:
            # make sure the path is correct
            page.path = wikipath

            self.db.update(page)

            if self.output:
                page.write(outroot)
        else:
            log.debug(f"Skipping {full_path}")
