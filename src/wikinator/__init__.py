import importlib.metadata
import logging
import json

import yaml
import typer
from typing import Optional
from typing_extensions import Annotated
import os
from dotenv import load_dotenv
import confuse

from wikinator.docxit import DocxitConverter
from wikinator.gdrive import GoogleDrive


from .wiki import GraphIngester, GraphDB


__app_name__ = "wikinator"
__app_version__ = importlib.metadata.version(__app_name__)


def load_config():
    template = {
        "db_url": "FIXME",
        "db_token": "FIXME",
        "log_level": "warning",
    }
    config = confuse.Configuration(__app_name__, __name__)
    config.set_env()
    return config.get(template)


def store_config(old_config):
    config = confuse.Configuration(__app_name__, __name__)
    config_filename = os.path.join(config.config_dir(), confuse.CONFIG_FILENAME)
    with open(config_filename, "w") as f:
        yaml.dump(config, f)


config = load_config()


log = logging.getLogger(__name__)


app = typer.Typer(add_completion=False)


class TyperLoggerHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        fg = None
        bg = None
        if record.levelno == logging.DEBUG:
            fg = typer.colors.CYAN
        elif record.levelno == logging.INFO:
            fg = typer.colors.BRIGHT_BLUE
        elif record.levelno == logging.WARNING:
            fg = typer.colors.BRIGHT_MAGENTA
        elif record.levelno == logging.CRITICAL:
            fg = typer.colors.BRIGHT_RED
        elif record.levelno == logging.ERROR:
            fg = typer.colors.BRIGHT_WHITE
            bg = typer.colors.RED
        typer.secho(self.format(record), bg=bg, fg=fg)


def init_logging(level:int) -> None:
    #fmt = "{asctime} {levelname:<8s} {name:<16} {message}"
    fmt = "{message}"
    typer_handler = TyperLoggerHandler()
    logging.basicConfig(level=logging.WARNING, format=fmt, style='{', handlers=(typer_handler,))
    # gql.transport.aiohttp = INFO for full transport logging
    log.setLevel(level)
    log.info(f"starting {__app_name__} v{__app_version__}")
    log.debug("debug logging enabled")


# initialize logging from config
init_logging(logging.getLevelName(config['log_level'].upper()))
log.debug(f"debug logging enabled {config}")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__app_version__}")
        raise typer.Exit()


def verbose_callback(value: bool) -> None:
    if value:
        init_logging(logging.INFO)


def debug_callback(value: bool) -> None:
    if value:
        init_logging(logging.DEBUG)


def trace_callback(value: bool) -> None:
    if value:
        init_logging(logging.DEBUG)
        comms_trace = logging.getLogger("gql.transport.aiohttp")
        comms_trace.setLevel(logging.INFO)


#- upload  : from files -> graphql
@app.command()
def upload(
    source: str,
    wikiroot: str = "/",
    db_url: Annotated[str, typer.Option("--db", help="URL of the GraphQL database")] = config['db_url'],
    db_token: Annotated[str, typer.Option("--token", help="URL of the GraphQL database")] = config['db_token'],
    output: Annotated[bool, typer.Option("-o", help="Make a local copy of the converted file")] = False,
) -> None:
    """
    Convert and upload a file hierarchy to a GraphQL wiki.
    Given a source directrory, walk the directory tree and
    for each file:
    - if MD or image file, upload at the same path relative to the wikiroot path
    - If DOCX, convert to MD and upload at the same path...
    - Unknown files are skipped.
    For example, with source=/src and wikiroot=/wiki/root,
    a DOCX file at /src/dir/some_file.docx will be uploaded to /wiki/root/dir/some_file on the wiki.
    """
    load_dotenv(dotenv_path=os.path.expanduser("~/.config/wikinator.env"))
    url = os.getenv("GRAPH_DB")
    token = os.getenv("AUTH_TOKEN")
    log.debug(f"Loaded env, db={url}")

    GraphIngester(url=url, token=token, output=output).convert_directory(source, wikiroot)


# Setup global options using callbacks
@app.callback()
def common(
    ctx: typer.Context,
    version: Annotated[bool, typer.Option("--version", callback=version_callback,
                                          help="Display version and exit.")] = False,
    verbose: Annotated[bool, typer.Option("-v", callback=verbose_callback,
                                          help="Show verbose logging.")] = False,
    debug: Annotated[bool, typer.Option("-vv", callback=debug_callback,
                                          help="Show debug logging.")] = False,
    trace: Annotated[bool, typer.Option("-vvv", callback=trace_callback,
                                          help="Show full trace logging.")] = False,
):
    pass


@app.command()
def convert(
    doc_url: Annotated[str, typer.Argument(help="URL of the google-doc")],
    db_url: Annotated[str, typer.Option("--db", help="URL of the GraphQL database. Defaults to $WIKINATOR_DB_URL")] = config['db_url'],
    path: Annotated[str, typer.Option("--path", help="Path to upload to. Defaults to '/' (root)")] = None,
    name: Annotated[str, typer.Option("--name", help="Name of the uploaded file. Defaults to '<document-name>.md'")] = None,
    token: Annotated[str, typer.Option("--token", help="Secure token for GraphQL database. Defaults to $WIKINATOR_DB_TOKEN")] = config['db_token'],
) -> None:
    """
    Given the URL of a specific gdoc:

    - download the document

    - convert it to markdown

    - upload the converted file to a GraphQL wiki with /path/name.

    Example:

        uvx wikinator example.com/docker_tutorials.docx --path edu/tutorials

    will create a new wiki entry '/edu/tutorials/docker_tutorials.md' from https://example.com/docker_tutorials.docx
    """
    log.debug(f"downloading {doc_url}")
    page = GoogleDrive().get_doc_url(doc_url)

    if name is not None:
        page.path = name

    log.debug(f"converting to {page.filename(path)}")
    # already done by get.

    log.debug(f"uploading to {db_url}/{page.filename(path)}")
    #db = GraphDB(db_url, token)
    #db.create(page)







#DocxitConverter().convert_directory(source, destination)

#- extract : from googledocs -> file system
# @app.command()
# def extract(
#     destination: Annotated[str, typer.Argument()] = "."
# ) -> None:
#     """
#     Extract one or more google drive docs to disk, in
#     markdown format.
#     url - the url of the doc or directory to recurse
#     destination - directory to extract to. defaults to current dir
#     """
#     # given a google-page-producer, store those pages
#     for page in GoogleDrive().list_files("application/vnd.google-apps.document"):
#         page.write(destination)


# #- teleport : from googledoc -> graphql
# @app.command()
# def teleport(
#     wikiroot: str,
#     # typer.Option(2, "--priority", "-p", min=1, max=3),
# ) -> None:
#     wiki = GraphDB()
#     for page in GoogleDrive().list_files("application/vnd.google-apps.document"):
#         wiki.upload(page, wikiroot)