""" Read metadata from image files using exiftool and 
write the data to Finder tags on MacOS.  Requires exiftool: 
https://exiftool.org/
"""

import pathlib
import sys

import click
import osxmetadata

from ._version import __version__
from .exiftool import ExifTool, get_exiftool_path

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
@click.option("--walk", help="Recursively walk directories")
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

    print(f"Processing {len(files)} files")
    for filename in files:
        file = pathlib.Path(filename)
        if file.is_dir():
            if walk:
                verbose(f"Processing directory {file}")
                process_directory(file, tag, tag_value, exiftool_path)
            else:
                verbose(f"Skipping directory {file}")
        else:
            verbose(f"Processing file {filename}")
            process_file(filename, tag, tag_value, exiftool_path)


def process_directory(dir, tags, tag_values, exiftool_path):
    """Process each directory applying exif metadata to extended attributes"""
    for path_object in pathlib.Path(dir).glob("**/*"):
        if path_object.is_file():
            verbose(f"Processing file {path_object}")
            process_file(path_object, tags, exiftool_path)
        elif path_object.is_dir():
            verbose(f"Processing directory {path_object}")
            process_directory(path_object, tags, exiftool_path)


def process_file(filename, tags, tag_values, exiftool_path):
    """Process each filename applying exif metadata to extended attributes"""
    exiftool = ExifTool(filename, exiftool=exiftool_path)
    exifdict = exiftool.asdict(tag_groups=False)
    exifdict.update(exiftool.asdict())

    # ExifTool returns dict with tag group names (e.g. IPTC:Keywords)
    # also add the tag names without group name
    finder_tags = []
    for tag, value in exifdict.items():
        if tag in tags:
            if isinstance(value, list):
                finder_tags.extend([f"{tag}: {v}" for v in value])
            else:
                finder_tags.append(f"{tag}: {value}")
        if tag in tag_values:
            if isinstance(value, list):
                finder_tags.extend([str(v) for v in value])
            else:
                finder_tags.append(str(value))

    verbose(f"Writing Finder tags {finder_tags} to {filename}")
    write_finder_tags(filename, finder_tags)


def write_finder_tags(filename, finder_tags):
    """Write Finder tags to file"""
    md = osxmetadata.OSXMetaData(filename)
    current_tags = list(md.tags)
    tags = [osxmetadata.Tag(tag) for tag in finder_tags]
    new_tags = [tag for tag in tags if tag not in current_tags]
    if new_tags:
        md.tags += new_tags


def main():
    cli()
