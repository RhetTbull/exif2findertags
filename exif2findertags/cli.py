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


class EXIFToFinderCommand(click.Command):
    """Custom click.Command that overrides get_help() to show additional help info for export"""

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()

        formatter.write("\n\n")
        formatter.write_text(
            "Tag names used with --tag and --tag-value may be any tag that exiftool can read. "
            + "For a complete list of tag values, see https://exiftool.org/TagNames/. "
            + "Tag names may be specified with or without the tag group name.  For example: "
            + "`--tag Keywords` and `--tag IPTC:Keywords` are both valid. "
            + "If specified, the group name will be output to the name of the Finder tag when used with --tag. "
            + "For example, `--tag IPTC:Keywords` will result in a Finder tag named `IPTC:Keywords: Travel` if `Travel` was one of the keywords "
            + "and `--tag Keywords` would result in a Finder tag of `Keywords: Travel`. "
            + "To use only the tag value as the keyword, use `--tag-value Keywords`, which would result in a Finder tag named `Travel`."
        )
        formatter.write("\n")
        formatter.write_text(
            "When used with --tag, Finder tags will be created in format `TagName: TagValue`. "
            + "For example, `--tag ISO` would produce something like `ISO: 100`. "
        )
        formatter.write("\n")
        formatter.write_text(
            "exiftool must be installed as it is used to read the metadata from media files. "
            + "See https://exiftool.org/ to download and install exiftool."
        )
        help_text += formatter.getvalue()
        return help_text


@click.command(cls=EXIFToFinderCommand)
@click.option("--verbose", "-V", "verbose_", is_flag=True, help="Show verbose output.")
@click.option(
    "--tag",
    multiple=True,
    help="Photo metadata tags to use as Finder tags; "
    + "multiple tags may be specified by repeating --tag, for example: `--tag Keywords --tag ISO`.",
)
@click.option(
    "--tag-value",
    multiple=True,
    help="Photo metadata tags to use as Finder tags; use only tag value as keyword; "
    + "multiple tags may be specified by repeating --tag-value, for example: `--tag-value Keywords --tag-value PersonInImage`.",
)
@click.option("--walk", is_flag=True, help="Recursively walk directories.")
@click.option(
    "--exiftool-path",
    type=click.Path(exists=True),
    default=get_exiftool_path(),
    help="Optional path to exiftool executable (will look in $PATH if not specified).",
)
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def cli(verbose_, tag, tag_value, walk, exiftool_path, files):
    """Create Finder tags from EXIF and other metadata in media files."""
    global VERBOSE
    VERBOSE = verbose_

    if not files or not (tag or tag_value):
        print_help_msg(cli)
        sys.exit(1)

    verbose(f"exiftool path: {exiftool_path}")

    # create nice looking text for status
    filenames = [file for file in files if pathlib.Path(file).is_file()]
    dirnames = [file for file in files if pathlib.Path(file).is_dir()]
    text = f'Processing {len(filenames)} {"file" if len(filenames) == 1 else "files"}'
    dirtext = (
        f' and {len(dirnames)} {"directory" if len(dirnames) == 1 else "directories"}'
    )
    text = text + dirtext if walk else text
    if dirnames and not walk and not filenames:
        click.echo(
            f"Found 0 files{dirtext} but --walk was not specified, nothing to do"
        )
        print_help_msg(cli)
        sys.exit(1)

    if not VERBOSE:
        with yaspin(text=text):
            files_updated = process_files(files, tag, tag_value, exiftool_path, walk)
    else:
        click.echo(text)
        files_updated = process_files(files, tag, tag_value, exiftool_path, walk)

    click.echo(
        f"Done. Updated metadata for {files_updated} {'file' if files_updated == 1 else 'files'}."
    )


def process_files(files, tag, tag_value, exiftool_path, walk) -> int:
    """Process files with ExifToFinder"""
    e2f = ExifToFinder(
        tags=tag,
        tag_values=tag_value,
        exiftool_path=exiftool_path,
        walk=walk,
        verbose=verbose,
    )

    files_processed = 0
    for filename in files:
        file = pathlib.Path(filename)
        if file.is_dir():
            if walk:
                verbose(f"Processing directory {file}")
                files_processed += e2f.process_directory(file)
            else:
                verbose(f"Skipping directory {file}")
        else:
            verbose(f"Processing file {file}")
            files_processed += e2f.process_file(file)
    return files_processed


def main():
    cli()
