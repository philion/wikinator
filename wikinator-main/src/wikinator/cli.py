from typing import Optional
import logging
from pathlib import Path

import typer
from typing_extensions import Annotated

from . import __app_name__, __app_version__
from .docxit import DocxitConverter
from .page import Page
from .gdrive import known_files, download_single_file, extract_file_id_from_url

app = typer.Typer()

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

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
    """Convert DOCX files to markdown format."""
    print("[DEBUG] Convert command started!")
    try:
        source_path = Path(source)
        dest_path = Path(destination)
        
        print(f"[DEBUG] Source path: {source_path}")
        print(f"[DEBUG] Destination path: {dest_path}")
        
        if not source_path.exists():
            typer.secho(f"Source path does not exist: {source}", fg=typer.colors.RED)
            raise typer.Exit(1)
        
        if source_path.is_file():
            print("[DEBUG] Processing single file")
            # Convert single file
            converter = DocxitConverter()
            page = converter.convert(source_path, source_path.parent, dest_path)
            if page:
                # Always write as out/<filename>.md, using absolute path
                abs_dest_path = dest_path.resolve()
                output_filename = abs_dest_path / (source_path.stem + ".md")
                print(f"[DEBUG] Absolute output directory: {abs_dest_path}")
                print(f"[DEBUG] Writing output to: {output_filename}")
                output_filename.parent.mkdir(parents=True, exist_ok=True)
                page.write_file(str(output_filename))
                print(f"[DEBUG] Finished writing output to: {output_filename}")
                typer.secho(f"Converted {source} to {output_filename}", fg=typer.colors.GREEN)
            else:
                typer.secho(f"Failed to convert {source}", fg=typer.colors.RED)
                raise typer.Exit(1)
        else:
            print("[DEBUG] Processing directory")
            # Convert directory
            converter = DocxitConverter()
            converter.convert_directory(source, destination)
            typer.secho(f"Converted files from {source} to {destination}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Error during conversion: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def extract(
    url: str = typer.Argument(..., help="Google Drive URL or file ID"),
    destination: Annotated[str, typer.Argument()] = "."
) -> None:
    """
    Extract Google Drive docs to disk in markdown format.
    
    URL can be:
    - A Google Drive sharing URL
    - A file ID
    - Empty (to extract all accessible Google Docs)
    """
    try:
        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)
        
        if url.strip():
            # Extract specific file or files from URL
            pages = known_files(url)
        else:
            # Extract all accessible Google Docs
            pages = known_files()
        
        if not pages:
            typer.secho("No Google Docs found to extract", fg=typer.colors.YELLOW)
            return
        
        for page in pages:
            try:
                page.write(destination)
                typer.secho(f"Extracted: {page.title} -> {page.path}", fg=typer.colors.GREEN)
            except Exception as e:
                typer.secho(f"Failed to write {page.title}: {e}", fg=typer.colors.RED)
        
        typer.secho(f"Extracted {len(pages)} document(s) to {destination}", fg=typer.colors.GREEN)
        
    except Exception as e:
        typer.secho(f"Error during extraction: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def upload(
    source: str = typer.Argument(..., help="Source file or directory"),
    destination: str = typer.Argument(..., help="Wiki.js URL"),
    token: str = typer.Option(None, "--token", "-t", help="Wiki.js API token"),
) -> None:
    """
    Upload markdown files to Wiki.js.
    
    This command will upload converted markdown files to a Wiki.js instance.
    """
    try:
        source_path = Path(source)
        if not source_path.exists():
            typer.secho(f"Source path does not exist: {source}", fg=typer.colors.RED)
            raise typer.Exit(1)
        
        # TODO: Implement Wiki.js upload functionality
        typer.secho("Upload functionality not yet implemented", fg=typer.colors.YELLOW)
        typer.secho(f"Would upload from {source} to {destination}", fg=typer.colors.BLUE)
        
    except Exception as e:
        typer.secho(f"Error during upload: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def teleport(
    source: str = typer.Argument(..., help="Google Drive URL or file ID"),
    destination: str = typer.Argument(..., help="Wiki.js URL"),
    token: str = typer.Option(None, "--token", "-t", help="Wiki.js API token"),
) -> None:
    """
    Teleport Google Docs directly to Wiki.js.
    
    Downloads Google Docs and uploads them directly to Wiki.js without saving to disk.
    """
    try:
        # Extract file ID from URL
        file_id = extract_file_id_from_url(source)
        if not file_id:
            typer.secho(f"Could not extract file ID from: {source}", fg=typer.colors.RED)
            raise typer.Exit(1)
        
        # Download the Google Doc
        page = download_single_file(file_id)
        if not page:
            typer.secho(f"Failed to download Google Doc: {source}", fg=typer.colors.RED)
            raise typer.Exit(1)
        
        typer.secho(f"Downloaded: {page.title}", fg=typer.colors.GREEN)
        
        # TODO: Implement direct upload to Wiki.js
        typer.secho("Direct upload to Wiki.js not yet implemented", fg=typer.colors.YELLOW)
        typer.secho(f"Would upload {page.title} to {destination}", fg=typer.colors.BLUE)
        
    except Exception as e:
        typer.secho(f"Error during teleport: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


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
    """
    Wikinator - Convert Google Docs and DOCX files to markdown and upload to Wiki.js.
    
    Supports:
    - Converting DOCX files to markdown
    - Extracting Google Docs to markdown
    - Uploading to Wiki.js (coming soon)
    """
    return
