import typer

from .docxit import DocxitConverter


# Thinking about commands:
# - convert : files -> files
# - extract : from googledocs -> file system
# - upload  : from files -> graphql
# - fullmonty : from googledoc -> graphql


def do_convert(src: str, dest: str = ".") -> None:
    DocxitConverter().convert_directory(src, dest)


def main() -> None:
    typer.run(do_convert)


if __name__ == "__main__":
    main()
