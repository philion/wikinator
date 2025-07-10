from typing import Optional

import typer
from typing_extensions import Annotated

from . import __app_name__, __app_version__
from .docxit import DocxitConverter
from .gdrive import GoogleDrive
from .wiki import GraphIngester, GraphDB

app = typer.Typer()

# TODO: init command, creates config with:
# - wiki url
# - wiki security token
# - google creds
# - and walk thru OAUTH r/t with google auth
# @app.command()
# def init(
#     db_path: str = typer.Option(
#         str(database.DEFAULT_DB_FILE_PATH),
#         "--db-path",
#         "-db",
#         prompt="to-do database location?",
#     ),
# ) -> None:
#     """Initialize the to-do database."""
#     app_init_error = config.init_app(db_path)
#     if app_init_error:
#         typer.secho(
#             f'Creating config file failed with "{ERRORS[app_init_error]}"',
#             fg=typer.colors.RED,
#         )
#         raise typer.Exit(1)
#     db_init_error = database.init_database(Path(db_path))
#     if db_init_error:
#         typer.secho(
#             f'Creating database failed with "{ERRORS[db_init_error]}"',
#             fg=typer.colors.RED,
#         )
#         raise typer.Exit(1)
#     else:
#         typer.secho(f"The to-do database is {db_path}", fg=typer.colors.GREEN)


@app.command()
def convert(
    source: str,
    destination: Annotated[str, typer.Argument()] = "."
) -> None:
    DocxitConverter().convert_directory(source, destination)


#- extract : from googledocs -> file system
@app.command()
def extract(
    destination: Annotated[str, typer.Argument()] = "."
) -> None:
    """
    Extract one or more google drive docs to disk, in
    markdown format.
    url - the url of the doc or directory to recurse
    destination - directory to extract to. defaults to current dir
    """
    # given a google-page-producer, store those pages
    for page in GoogleDrive().list_files("application/vnd.google-apps.document"):
        page.write(destination)


#- upload  : from files -> graphql
@app.command()
def upload(
    source: str,
    wikiroot: str,
    # typer.Option(2, "--priority", "-p", min=1, max=3),
) -> None:

    uploader = GraphIngester()
    uploader.convert_directory(source, wikiroot)


#- teleport : from googledoc -> graphql
@app.command()
def teleport(
    wikiroot: str,
    # typer.Option(2, "--priority", "-p", min=1, max=3),
) -> None:
    wiki = GraphDB()
    for page in GoogleDrive().list_files("application/vnd.google-apps.document"):
        wiki.upload(page, wikiroot)


# @app.command()
# def remove(
#     todo_id: int = typer.Argument(...),
#     force: bool = typer.Option(
#         False,
#         "--force",
#         "-f",
#         help="Force deletion without confirmation.",
#     ),
# ) -> None:


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__app_version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    return
