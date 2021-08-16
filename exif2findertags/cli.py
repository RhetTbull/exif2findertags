""" Read metadata from image files using exiftool and 
write the data to Finder tags on MacOS.  Requires exiftool: 
https://exiftool.org/
"""

import pathlib
import sys
import argparse
import osxmetadata

from ._version import __version__
from .exiftool import ExifTool, get_exiftool_path

# if True, shows verbose output, controlled via --verbose flag
VERBOSE = False


def verbose(message_str, **kwargs):
    if not VERBOSE:
        return
    print(message_str, **kwargs)


def error(error_str):
    print(error_str, file=sys.stderr)


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose", help="increase output verbosity", action="store_true"
    )
    parser.add_argument(
        "--exiftool-path",
        help="specify path to exiftool",
    )
    parser.add_argument("--walk", help="Recursively walk directories and process files")
    parser.add_argument("files", help="files to process", nargs="+")
    args = parser.parse_args()

    global VERBOSE
    VERBOSE = args.verbose

    if not args.files:
        print("Help")

    if not args.exiftool_path:
        exiftool_path = get_exiftool_path()
    verbose(f"exiftool path: {args.exiftool_path}")

    print(f"Processing {len(args.files)} files")
    for filename in args.files:
        file = pathlib.Path(filename)
        if file.is_dir():
            if args.walk:
                verbose(f"Processing directory {file}")
                process_directory(file, args.exiftool_path)
            else:
                verbose(f"Skipping directory {file}")
        else:
            verbose(f"Processing file {filename}")
            process_file(filename, args.exiftool_path)


def process_directory(dir, exiftool_path):
    """Process each directory applying exif metadata to extended attributes"""
    for path_object in pathlib.Path(dir).glob("**/*"):
        if path_object.is_file():
            verbose(f"Processing file {path_object}")
            process_file(path_object, exiftool_path)
        elif path_object.is_dir():
            verbose(f"Processing directory {path_object}")
            process_directory(path_object, exiftool_path)


def process_file(filename, exiftool_path):
    """Process each filename applying exif metadata to extended attributes"""
    exiftool = ExifTool(filename, exiftool=exiftool_path)
    exifdict = exiftool.asdict(tag_groups=False)

    # ExifTool returns dict with tag group names (e.g. IPTC:Keywords)
    # also add the tag names without group name
    for tag, value in exifdict.items():
        print(f"{tag} {value}")

        # TODO: select the tags to write as Finder tags
        # write the tags with osxmetadata
