""" Read metadata from image files using exiftool and 
write the data to Finder tags on MacOS.  Requires exiftool: 
https://exiftool.org/
"""

import io
import pathlib
import re
import sys

import click
from cloup import (
    Command,
    Context,
    HelpFormatter,
    HelpTheme,
    Style,
    argument,
    command,
    option,
    option_group,
    version_option,
)
from cloup.constraints import RequireAtLeast, mutually_exclusive
from rich.console import Console
from rich.markdown import Markdown
from yaspin import yaspin

from ._version import __version__
from .exiftofinder import DEFAULT_GROUP_TAG_TEMPLATE, DEFAULT_TAG_TEMPLATE, ExifToFinder
from .exiftool import get_exiftool_path
from .phototemplate import TEMPLATE_SUBSTITUTIONS_ALL, get_template_help

# if True, shows verbose output, controlled via --verbose flag
VERBOSE = False


def verbose(message_str, **kwargs):
    if not VERBOSE:
        return
    print(message_str, **kwargs)


def print_help_msg(command):
    with Context(command) as ctx:
        click.echo(command.get_help(ctx))


class EXIFToFinderCommand(Command):
    """Custom cloup.command that overrides get_help() to show additional help info for export"""

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = HelpFormatter()

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

        formatter.write("\n\n")
        formatter.write(
            rich_text("[bold]** Template System **[/bold]", width=formatter.width)
        )
        formatter.write("\n")
        formatter.write(template_help(width=formatter.width))
        formatter.write("\n")
        formatter.write(
            rich_text(
                "[bold]** Template Substitutions **[/bold]", width=formatter.width
            )
        )
        formatter.write("\n")
        templ_tuples = [("Substitution", "Description")]
        templ_tuples.extend((k, v) for k, v in TEMPLATE_SUBSTITUTIONS_ALL.items())
        formatter.write_dl(templ_tuples)

        help_text += formatter.getvalue()
        return help_text


formatter_settings = HelpFormatter.settings(
    theme=HelpTheme(
        invoked_command=Style(fg="bright_yellow"),
        heading=Style(fg="bright_white", bold=True),
        constraint=Style(fg="magenta"),
        col1=Style(fg="bright_yellow"),
    )
)


@command(cls=EXIFToFinderCommand, formatter_settings=formatter_settings)
@option_group(
    "Specify which metadata tags to export to Finder tags and/or comments",
    option(
        "--tag",
        metavar="TAG",
        multiple=True,
        help="Photo metadata tags to use as Finder tags; "
        + "multiple tags may be specified by repeating --tag, for example: `--tag Keywords --tag ISO`. "
        + "Finder tags will be in form 'TAG: VALUE', e.g. 'ISO: 80' or 'IPTC:Keywords: Travel'. "
        + "If the group name is specified it will be included in the Finder tag name, otherwise, "
        + "just the tag name will be included. ",
    ),
    option(
        "--tag-value",
        metavar="TAG",
        multiple=True,
        help="Photo metadata tags to use as Finder tags; use only tag value as keyword; "
        + "multiple tags may be specified by repeating --tag-value, for example: `--tag-value Keywords --tag-value PersonInImage`.",
    ),
    option(
        "--all-tags",
        is_flag=True,
        help="Include all metadata found in file as Finder tags; see also, --group, --value.",
    ),
    option(
        "--tag-group",
        multiple=True,
        metavar="GROUP",
        help="Include all metadata from GROUP tag group, e.g. '--tag-group EXIF', '--tag-group XMP'; see also, --group, --value.",
    ),
    option(
        "--tag-match",
        multiple=True,
        metavar="PATTERN",
        help="Include all metadata tags whose tag name matches PATTERN, e.g. '--tag-match Exposure'; see also, --group, --value. "
        + "PATTERN is case-sensitive, e.g. '--tag-match Exposure' matches EXIF:ExposureTime, EXIF:ExposureMode, etc. but '--tag-match exposure' would not; "
        + "see also, --group, --value",
    ),
    option(
        "--fc",
        metavar="TAG",
        multiple=True,
        help="Photo metadata tags to use as Finder comments; "
        + "multiple tags may be specified by repeating --fc, for example: `--fc Keywords --fc ISO`. "
        + "Tags will be appended to Finder comment. "
        + "If the group name is specified it will be included in the Finder comment, otherwise, "
        + "just the tag name will be included.",
    ),
    option(
        "--fc-value",
        metavar="TAG",
        multiple=True,
        help="Photo metadata tags to use as Finder comments; use only tag value as comment; "
        + "multiple tags may be specified by repeating --fc-value, for example: `--fc-value Keywords --fc-value PersonInImage`. "
        + "Tag values will be appended to Finder comment.",
    ),
    constraint=RequireAtLeast(1),
)
@option_group(
    "Formatting options",
    option(
        "--tag-format",
        metavar="TEMPLATE",
        help="Template for specifying Finder tag format. "
        "'{GROUP}' will be replaced with group name of tag (as specified by exiftool), '{TAG}' will be replaced by tag name, "
        "and '{VALUE}' will be replaced by the tag value. "
        f"Default tag template is '{DEFAULT_GROUP_TAG_TEMPLATE}' if tag group specified otherwise '{DEFAULT_TAG_TEMPLATE}'. "
        "See Template System for additional details.",
    ),
    option(
        "--fc-format",
        metavar="TEMPLATE",
        help="Template for specifying Finder comment format. "
        "'{GROUP}' will be replaced with group name of tag (as specified by exiftool), '{TAG}' will be replaced by tag name, "
        "and '{VALUE}' will be replaced by the tag value. "
        f"Default Finder comment template is '{DEFAULT_GROUP_TAG_TEMPLATE}' if tag group specified otherwise '{DEFAULT_TAG_TEMPLATE}'. "
        "See Template System for additional details.",
    ),
)
@option_group(
    "Options for use with --all-tags, --tag-group, --tag-match",
    option(
        "--group",
        "-G",
        is_flag=True,
        help="Include tag group in Finder tag (for example, 'EXIF:Make' instead of 'Make') when used with --all-tags --tag-group, --tag-match.",
    ),
    option(
        "--value",
        is_flag=True,
        help="Use only tag value (not tag name) as Finder tag when used with --all-tags.",
    ),
    constraint=mutually_exclusive,
)
@option_group(
    "Settings",
    option("--verbose", "-V", "verbose_", is_flag=True, help="Show verbose output."),
    option("--walk", is_flag=True, help="Recursively walk directories."),
    option(
        "--exiftool-path",
        type=click.Path(exists=True),
        default=get_exiftool_path(),
        help="Optional path to exiftool executable (will look in $PATH if not specified).",
    ),
    option(
        "--dry-run",
        is_flag=True,
        help="Dry run mode; do not actually modify any Finder metadata.",
    ),
    option(
        "--overwrite-tags",
        is_flag=True,
        help="Overwrite existing Finder tags (default is to append to existing).",
    ),
    option(
        "--overwrite-fc",
        is_flag=True,
        help="Overwrite existing Finder comments (default is to append to existing).",
    ),
)
@version_option(version=__version__)
@argument("files", nargs=-1, type=click.Path(exists=True))
def cli(
    verbose_,
    tag,
    tag_value,
    walk,
    exiftool_path,
    files,
    all_tags,
    tag_format,
    group,
    value,
    tag_group,
    tag_match,
    fc,
    fc_value,
    dry_run,
    fc_format,
    overwrite_tags,
    overwrite_fc,
):
    """Create Finder tags and/or Finder comments from EXIF and other metadata in media files."""
    global VERBOSE
    VERBOSE = verbose_

    if not files:
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
            files_updated = process_files(
                files=files,
                tag=tag,
                tag_value=tag_value,
                exiftool_path=exiftool_path,
                walk=walk,
                all_tags=all_tags,
                group=group,
                tag_format=tag_format,
                fc_format=fc_format,
                value=value,
                tag_group=tag_group,
                tag_match=tag_match,
                fc=fc,
                fc_value=fc_value,
                dry_run=dry_run,
                overwrite_tags=overwrite_tags,
                overwrite_fc=overwrite_fc,
            )
    else:
        click.echo(text)
        files_updated = process_files(
            files=files,
            tag=tag,
            tag_value=tag_value,
            exiftool_path=exiftool_path,
            walk=walk,
            all_tags=all_tags,
            group=group,
            tag_format=tag_format,
            fc_format=fc_format,
            value=value,
            tag_group=tag_group,
            tag_match=tag_match,
            fc=fc,
            fc_value=fc_value,
            dry_run=dry_run,
            overwrite_tags=overwrite_tags,
            overwrite_fc=overwrite_fc,
        )

    click.echo(
        f"Done. Updated metadata for {files_updated} {'file' if files_updated == 1 else 'files'}."
    )


def process_files(
    files,
    tag,
    tag_value,
    exiftool_path,
    walk,
    all_tags,
    group,
    tag_format,
    fc_format,
    value,
    tag_group,
    tag_match,
    fc,
    fc_value,
    dry_run,
    overwrite_tags,
    overwrite_fc,
) -> int:
    """Process files with ExifToFinder"""
    e2f = ExifToFinder(
        tags=tag,
        tag_values=tag_value,
        exiftool_path=exiftool_path,
        walk=walk,
        verbose=verbose,
        all_tags=all_tags,
        group=group,
        value=value,
        tag_groups=tag_group,
        tag_match=tag_match,
        fc_tags=fc,
        fc_tag_values=fc_value,
        dry_run=dry_run,
        tag_format=tag_format,
        fc_format=fc_format,
        overwrite_tags=overwrite_tags,
        overwrite_fc=overwrite_fc,
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


def rich_text(text, width=78):
    """Return rich formatted text"""
    sio = io.StringIO()
    console = Console(file=sio, force_terminal=True, width=width)
    console.print(text)
    rich_text = sio.getvalue()
    sio.close()
    return rich_text


def strip_md_header_and_links(md):
    """strip markdown headers and links from markdown text md

    Args:
        md: str, markdown text

    Returns:
        str with markdown headers and links removed

    Note: This uses a very basic regex that likely fails on all sorts of edge cases
    but works for the links in the osxphotos docs
    """
    links = r"(?:[*#])|\[(.*?)\]\(.+?\)"

    def subfn(match):
        return match.group(1)

    return re.sub(links, subfn, md)


def strip_md_links(md):
    """strip markdown links from markdown text md

    Args:
        md: str, markdown text

    Returns:
        str with markdown links removed

    Note: This uses a very basic regex that likely fails on all sorts of edge cases
    but works for the links in the osxphotos docs
    """
    links = r"\[(.*?)\]\(.+?\)"

    def subfn(match):
        return match.group(1)

    return re.sub(links, subfn, md)


def strip_html_comments(text):
    """Strip html comments from text (which doesn't need to be valid HTML)"""
    return re.sub(r"<!--(.|\s|\n)*?-->", "", text)


def template_help(width=78):
    """Return formatted string for template system"""
    sio = io.StringIO()
    console = Console(file=sio, force_terminal=True, width=width)
    template_help_md = strip_md_header_and_links(get_template_help())
    console.print(Markdown(template_help_md))
    help_str = sio.getvalue()
    sio.close()
    return help_str


def main():
    cli()
