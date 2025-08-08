import importlib.metadata
import logging
import typer
from typing import Optional
from typing_extensions import Annotated

from .wiki import GraphIngester


__app_name__ = "wikinator"
__app_version__ = importlib.metadata.version(__app_name__)


log = logging.getLogger(__name__)

app = typer.Typer(add_completion=False)


class TyperLoggerHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        fg = None
        bg = None
        if record.levelno == logging.DEBUG:
            fg = typer.colors.BLACK
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
    logging.basicConfig(level=level, format=fmt, style='{', handlers=(typer_handler,))
    log.setLevel(level)
    log.info(f"starting {__app_name__} v{__app_version__}")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__app_version__}")
        raise typer.Exit()


def verbose_callback(value: bool) -> None:
    if value:
        init_logging(logging.DEBUG)
    else:
        init_logging(logging.WARNING)


# @app.command()
# def hello(
#     name: Annotated[str, typer.Option()] = "World",
#     version: Annotated[
#         Optional[bool], typer.Option("--version", callback=version_callback)
#     ] = None,
#     ):
#     """Say hello to someone."""
#     typer.echo(f"👋 Hello, {name}!")


#- upload  : from files -> graphql
@app.command()
def upload(
    source: str,
    wikiroot: str,
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
    uploader = GraphIngester()
    uploader.convert_directory(source, wikiroot)


@app.callback()
def common(
    ctx: typer.Context,
    version: Annotated[bool, typer.Option("--version", callback=version_callback,
                                          help="Display version and exit.")] = False,
    verbose: Annotated[bool, typer.Option("-v", callback=verbose_callback,
                                          help="Show verbose logging.")] = False,
):
    pass



# TODO


# @app.command()
# def convert(
#     source: str,
#     destination: Annotated[str, typer.Argument()] = "."
# ) -> None:
#     DocxitConverter().convert_directory(source, destination)


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