""" ExifToFinder class """

import pathlib

import osxmetadata

from .exiftool import ExifTool, get_exiftool_path


def noop():
    """Do nothing"""
    pass


class ExifToFinder:
    """Read EXIF and other photo/video metadata with exiftool and write to Finder tags"""

    def __init__(self, tags, tag_values, exiftool_path, walk, verbose=None) -> None:
        self.tags = tags
        self.tag_values = tag_values
        self.exiftool_path = exiftool_path or get_exiftool_path()
        self.walk = walk
        self.verbose = verbose or noop
        if not callable(verbose):
            raise ValueError("verbose must be callable")

    def process_directory(self, dir):
        """Process each directory applying exif metadata to extended attributes"""
        for path_object in pathlib.Path(dir).glob("**/*"):
            if path_object.is_file():
                self.verbose(f"Processing file {path_object}")
                self.process_file(path_object)
            elif path_object.is_dir():
                self.verbose(f"Processing directory {path_object}")
                self.process_directory(path_object)

    def process_file(self, filename):
        """Process each filename applying exif metadata to extended attributes"""
        exiftool = ExifTool(filename, exiftool=self.exiftool_path)
        exifdict = exiftool.asdict(tag_groups=False)
        exifdict.update(exiftool.asdict())

        # ExifTool returns dict with tag group names (e.g. IPTC:Keywords)
        # also add the tag names without group name
        finder_tags = []
        for tag, value in exifdict.items():
            if tag in self.tags:
                if isinstance(value, list):
                    finder_tags.extend([f"{tag}: {v}" for v in value])
                else:
                    finder_tags.append(f"{tag}: {value}")
            if tag in self.tag_values:
                if isinstance(value, list):
                    finder_tags.extend([str(v) for v in value])
                else:
                    finder_tags.append(str(value))

        self.verbose(f"Writing Finder tags {finder_tags} to {filename}")
        self.write_finder_tags(filename, finder_tags)

    def write_finder_tags(self, filename, finder_tags):
        """Write Finder tags to file"""
        md = osxmetadata.OSXMetaData(filename)
        current_tags = list(md.tags)
        tags = [osxmetadata.Tag(tag) for tag in finder_tags]
        new_tags = [tag for tag in tags if tag not in current_tags]
        if new_tags:
            md.tags += new_tags
