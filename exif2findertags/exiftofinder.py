""" ExifToFinder class """

import pathlib

import osxmetadata

from .exiftool import ExifToolCaching, get_exiftool_path
from .phototemplate import PhotoTemplate, RenderOptions


def noop():
    """Do nothing"""
    pass


DEFAULT_GROUP_TAG_TEMPLATE = "{GROUP}:{TAG}: {VALUE}"
DEFAULT_TAG_TEMPLATE = "{TAG}: {VALUE}"


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
        tag_match=None,
        fc_tags=None,
        fc_tag_values=None,
        dry_run=False,
        tag_format=None,
        fc_format=None,
        overwrite_tags=False,
        overwrite_fc=False,
        tag_template=None,
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
        tag_match: a case sensitive pattern to match against tag names
        fc_tags: list of tags to write to Finder comments
        fc_tag_values: list of tag values to write to Finder comments
        dry_run: run in dry-run mode (don't write anything)
        tag_format: template string for writing Finder tags
        fc_format: template string for writing Finder comments
        overwrite_tags: overwrite existing Finder tags
        overwrite_fc: overwrite existing Finder comments
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
        self.tag_match = tag_match
        self.fc_tags = fc_tags
        self.fc_tag_values = fc_tag_values
        self.dry_run = dry_run
        self.tag_format = tag_format
        self.fc_format = fc_format
        self.overwrite_tags = overwrite_tags
        self.overwrite_fc = overwrite_fc
        self.tag_template = tag_template

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
        exiftool = ExifToolCaching(filename, exiftool=self.exiftool_path)
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
                rendered = self.format_tag_value(filename, tag_name, exiftool)
                finder_tags.extend(rendered)
        for tag_value in self.tag_values:
            tag_name = exifdict_lc.get(tag_value.lower())
            if tag_name:
                value = exifdict[tag_name]
                finder_tags.extend(exif_values_to_list(value))

        if self.all_tags or self.tag_groups or self.tag_match:
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

                if self.tag_match and all(m not in tag_name for m in self.tag_match):
                    continue

                if self.group:
                    rendered = self.format_tag_value(filename, tag, exiftool)
                    finder_tags.extend(rendered)
                elif self.value:
                    finder_tags.extend(exif_values_to_list(value))
                else:
                    rendered = self.format_tag_value(filename, tag_name, exiftool)
                    finder_tags.extend(rendered)

        if self.tag_template:
            for template in self.tag_template:
                rendered = self.render_template(template, filename, exiftool)
                finder_tags.extend(rendered)

        # eliminate duplicates
        finder_tags = list(set(finder_tags))
        file_count = 0
        if finder_tags:
            self.verbose(f"Writing Finder tags {finder_tags} to {filename}")
            self.write_finder_tags(filename, finder_tags)
            file_count = 1
        else:
            self.verbose(f"No Finder tags to write to {filename}")

        finder_comment = []
        for tag in self.fc_tags:
            tag_name = exifdict_lc.get(tag.lower())
            if tag_name:
                value = exifdict[tag_name]
                rendered = self.format_fc_value(filename, tag_name, exiftool)
                finder_comment.extend(rendered)
        for tag_value in self.fc_tag_values:
            tag_name = exifdict_lc.get(tag_value.lower())
            if tag_name:
                value = exifdict[tag_name]
                finder_comment.extend(exif_values_to_list(value))

        comment = "\n".join(finder_comment)
        if comment:
            self.verbose(f"Writing Finder comment {comment} to {filename}")
            self.write_finder_comment(filename, comment)
            file_count = 1

        return file_count

    def write_finder_tags(self, filename, finder_tags):
        """Write Finder tags to file"""
        if self.dry_run:
            return
        md = osxmetadata.OSXMetaData(filename)
        current_tags = list(md.tags)
        tags = [osxmetadata.Tag(tag) for tag in finder_tags]
        if self.overwrite_tags:
            new_tags = tags
        else:
            new_tags = current_tags + [tag for tag in tags if tag not in current_tags]
        if new_tags:
            md.tags = new_tags

    def write_finder_comment(self, filename, comment):
        """Write Finder comment to file"""
        if self.dry_run:
            return
        md = osxmetadata.OSXMetaData(filename)
        fc = md.findercomment
        if self.overwrite_fc:
            md.findercomment = comment
        else:
            md.findercomment = fc + "\n" + comment if fc else comment

    def format_tag_value(self, filename, tag, exiftool):
        """Format a tag value with a template"""
        template = self.tag_format or (
            DEFAULT_GROUP_TAG_TEMPLATE if ":" in tag else DEFAULT_TAG_TEMPLATE
        )
        return self._format_value_with_template(template, filename, tag, exiftool)

    def format_fc_value(self, filename, tag, exiftool):
        """Format a Finder comment value with a template"""
        template = self.fc_format or (
            DEFAULT_GROUP_TAG_TEMPLATE if ":" in tag else DEFAULT_TAG_TEMPLATE
        )
        return self._format_value_with_template(template, filename, tag, exiftool)

    def _format_value_with_template(self, template, filename, tag, exiftool):
        """Format a tag value with a template"""
        phototemplate = PhotoTemplate(filename)
        options = RenderOptions(tag=tag, exiftool=exiftool, filepath=filename)
        rendered, _ = phototemplate.render(template, options)
        return rendered

    def render_template(self, template, filename, exiftool):
        """Render a template"""
        phototemplate = PhotoTemplate(filename)
        options = RenderOptions(tag=None, exiftool=exiftool, filepath=filename)
        rendered, _ = phototemplate.render(template, options)
        return rendered


def exif_values_to_list(value):
    """Convert a value returned by ExifTool to a list if it is not already and filter out bad data"""
    if isinstance(value, list):
        value = [v for v in value if not str(v).startswith("(Binary data ")]
        return [str(v) for v in value]
    elif not str(value).startswith("(Binary data "):
        return [str(value)]
