""" ExifToFinder class """

import pathlib

import osxmetadata

from .exiftool import ExifTool, get_exiftool_path


def noop():
    """Do nothing"""
    pass


class ExifToFinder:
    """Read EXIF and other photo/video metadata with exiftool and write to Finder tags"""

    def __init__(
        self,
        tags=None,
        tag_values=None,
        exiftool_path=None,
        walk=False,
        verbose=None,
        all_tags=False,
        group=False,
        value=False,
        tag_groups=None,
    ) -> None:
        """Args:
        tags: list of tags to read from EXIF
        tag_values: list of tag values to read from EXIF (don't include tag names in Finder tags)
        exiftool_path: path to exiftool executable
        walk: whether to walk directories recursively
        verbose: whether to print verbose output
        all_tags: whether to use all tags found in file
        group: whether to use tag groups as Finder tag names (e.g. IPTC:Keywords instead of Keywords) when used with all_tags
        value: whether to use tag values as Finder tag names when used with all_tags
        tag_groups: list of tag groups to use as Finder tag names (e.g. IPTC or EXIF)
        """
        self.tags = tags
        self.tag_values = tag_values
        self.exiftool_path = exiftool_path or get_exiftool_path()
        self.walk = walk
        self.verbose = verbose or noop
        self.all_tags = all_tags
        self.group = group
        self.value = value
        self.tag_groups = tag_groups
        if self.tag_groups:
            self.tag_groups = [tag.lower() for tag in self.tag_groups]

        if not callable(verbose):
            raise ValueError("verbose must be callable")

    def process_directory(self, dir, _files_processed=0):
        """Process each directory applying exif metadata to extended attributes"""
        for path_object in pathlib.Path(dir).glob("**/*"):
            if path_object.is_file():
                self.verbose(f"Processing file {path_object}")
                self.process_file(path_object)
                _files_processed += 1
            elif path_object.is_dir():
                self.verbose(f"Processing directory {path_object}")
                self.process_directory(path_object, _files_processed)
        return _files_processed

    def process_file(self, filename):
        """Process each filename applying exif metadata to extended attributes"""
        exiftool = ExifTool(filename, exiftool=self.exiftool_path)
        exifdict_no_groups = exiftool.asdict(tag_groups=False)
        exifdict_groups = exiftool.asdict()
        exifdict = exifdict_no_groups.copy()
        exifdict.update(exifdict_groups)
        exifdict_lc = {k.lower(): k for k in exifdict}

        # ExifTool returns dict with tag group names (e.g. IPTC:Keywords)
        # also add the tag names without group name

        # "(Binary data " below is hack workaround for "(Binary data 0 bytes, use -b option to extract)" error that happens
        # when exporting video with keywords on Photos 5.0 / Catalina

        # TODO: refactor out the duplicate code

        finder_tags = []
        for tag in self.tags:
            tag_name = exifdict_lc.get(tag.lower())
            if tag_name:
                value = exifdict[tag_name]
                if isinstance(value, list):
                    value = [v for v in value if not str(v).startswith("(Binary data ")]
                    finder_tags.extend([f"{tag_name}: {v}" for v in value])
                elif not str(value).startswith("(Binary data "):
                    finder_tags.append(f"{tag_name}: {value}")
        for tag_value in self.tag_values:
            tag_name = exifdict_lc.get(tag_value.lower())
            if tag_name:
                value = exifdict[tag_name]
                if isinstance(value, list):
                    value = [v for v in value if not str(v).startswith("(Binary data ")]
                    finder_tags.extend([str(v) for v in value])
                elif not str(value).startswith("(Binary data "):
                    finder_tags.append(str(value))

        if self.all_tags or self.tag_groups:
            # process all tags or specific tag groups
            for tag in exifdict_groups:
                if tag == "SourceFile":
                    continue
                group, tag_name = tag.split(":", 1)
                if group in ["File", "ExifTool"]:
                    continue
                value = exifdict_groups[tag]
                if self.tag_groups and group.lower() not in self.tag_groups:
                    continue
                if self.group:
                    if isinstance(value, list):
                        value = [
                            v for v in value if not str(v).startswith("(Binary data ")
                        ]
                        finder_tags.extend([f"{tag}: {v}" for v in value])
                    elif not str(value).startswith("(Binary data "):
                        finder_tags.append(f"{tag}: {value}")
                elif self.value:
                    if isinstance(value, list):
                        value = [
                            v for v in value if not str(v).startswith("(Binary data ")
                        ]
                        finder_tags.extend([str(v) for v in value])
                    elif not str(value).startswith("(Binary data "):
                        finder_tags.append(str(value))
                else:
                    if isinstance(value, list):
                        value = [
                            v for v in value if not str(v).startswith("(Binary data ")
                        ]
                        finder_tags.extend([f"{tag_name}: {v}" for v in value])
                    elif not str(value).startswith("(Binary data "):
                        finder_tags.append(f"{tag_name}: {value}")


        # eliminate duplicates
        finder_tags = list(set(finder_tags))

        if finder_tags:
            self.verbose(f"Writing Finder tags {finder_tags} to {filename}")
            self.write_finder_tags(filename, finder_tags)
            return 1
        else:
            self.verbose(f"No Finder tags to write to {filename}")
            return 0

    def write_finder_tags(self, filename, finder_tags):
        """Write Finder tags to file"""
        md = osxmetadata.OSXMetaData(filename)
        current_tags = list(md.tags)
        tags = [osxmetadata.Tag(tag) for tag in finder_tags]
        new_tags = current_tags + [tag for tag in tags if tag not in current_tags]
        if new_tags:
            md.tags = new_tags
