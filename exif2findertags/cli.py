""" Read metadata from image files using exiftool and 
write the data to Finder tags on MacOS.  Requires exiftool: 
https://exiftool.org/
"""

import pathlib
import sys

import click
from yaspin import yaspin

from ._version import __version__
from .exiftofinder import ExifToFinder
from .exiftool import get_exiftool_path

# if True, shows verbose output, controlled via --verbose flag
VERBOSE = False


def verbose(message_str, **kwargs):
    if not VERBOSE:
        return
    print(message_str, **kwargs)


def print_help_msg(command):
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


@click.command()
@click.option("--verbose", "-V", "verbose_", is_flag=True, help="Show verbose output")
@click.option("--tag", multiple=True, help="Photo metadata tags to use as Finder tags")
@click.option(
    "--tag-value",
    multiple=True,
    help="Photo metadata tags to use as Finder tags; use only tag value as keyword",
)
@click.option("--walk", is_flag=True, help="Recursively walk directories")
@click.option(
    "--exiftool-path",
    type=click.Path(exists=True),
    default=get_exiftool_path(),
    help="Optional path to exiftool executable (will look in $PATH if not specified)",
)
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def cli(verbose_, tag, tag_value, walk, exiftool_path, files):
    """CLI interface"""
    global VERBOSE
    VERBOSE = verbose_

    if not files or not (tag or tag_value):
        print_help_msg(cli)
        sys.exit(1)

    verbose(f"exiftool path: {exiftool_path}")

    filenames = [file for file in files if pathlib.Path(file).is_file()]
    dirnames = [file for file in files if pathlib.Path(file).is_dir()]
    text = f'Processing {len(filenames)} {"file" if len(filenames) == 1 else "file"} and {len(dirnames)} {"directory" if len(dirnames) == 1 else "directories"}'
    if not VERBOSE:
        with yaspin(text=text):
            process_files(files, tag, tag_value, exiftool_path, walk)
    else:
        print(text)
        process_files(files, tag, tag_value, exiftool_path, walk)


def process_files(files, tag, tag_value, exiftool_path, walk):
    """Process files with ExifToFinder"""
    e2f = ExifToFinder(
        tags=tag,
        tag_values=tag_value,
        exiftool_path=exiftool_path,
        walk=walk,
        verbose=verbose,
    )

    for filename in files:
        file = pathlib.Path(filename)
        if file.is_dir():
            if walk:
                verbose(f"Processing directory {file}")
                e2f.process_directory(file)
            else:
                verbose(f"Skipping directory {file}")
        else:
            verbose(f"Processing file {file}")
            e2f.process_file(file)


def main():
    cli()
