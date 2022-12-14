""" ExifToFinder class """

import pathlib

import osxmetadata
from osxmetadata import MDITEM_ATTRIBUTE_DATA, MDITEM_ATTRIBUTE_SHORT_NAMES

from .exiftool import ExifToolCaching, get_exiftool_path
from .phototemplate import PhotoTemplate, RenderOptions


def noop():
    """Do nothing"""
    pass


DEFAULT_GROUP_TAG_TEMPLATE = "{GROUP}:{TAG}: {VALUE}"
DEFAULT_TAG_TEMPLATE = "{TAG}: {VALUE}"

# supported attributes for xattr_template
EXTENDED_ATTRIBUTE_NAMES = [
    "authors",
    "comment",
    "copyright",
    "creator",
    "description",
    "findercomment",
    "headline",
    "keywords",
    "participants",
    "projects",
    "rating",
    "subject",
    "title",
    "version",
]
EXTENDED_ATTRIBUTE_NAMES_QUOTED = [f"'{x}'" for x in EXTENDED_ATTRIBUTE_NAMES]


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
        fc_template=None,
        xattr_template=None,
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
        tag_template: list of template strings for writing Finder tags
        fc_template: list of template strings for writing Finder comments
        xattr_template: list of template tuples (attribute, template) for writing extended attributes
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
        self.fc_template = fc_template
        self.xattr_template = xattr_template

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
            if tag_name := exifdict_lc.get(tag.lower()):
                rendered = self.format_tag_value(filename, tag_name, exiftool)
                finder_tags.extend(rendered)

        for tag_value in self.tag_values:
            if tag_name := exifdict_lc.get(tag_value.lower()):
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

        file_count = 0
        if finder_tags := list(set(finder_tags)):
            self.verbose(f"Writing Finder tags {finder_tags} to {filename}")
            self.write_finder_tags(filename, finder_tags)
            file_count = 1
        else:
            self.verbose(f"No Finder tags to write to {filename}")

        finder_comment = []
        for tag in self.fc_tags:
            if tag_name := exifdict_lc.get(tag.lower()):
                value = exifdict[tag_name]
                rendered = self.format_fc_value(filename, tag_name, exiftool)
                finder_comment.extend(rendered)

        for tag_value in self.fc_tag_values:
            if tag_name := exifdict_lc.get(tag_value.lower()):
                value = exifdict[tag_name]
                finder_comment.extend(exif_values_to_list(value))

        if self.fc_template:
            for template in self.fc_template:
                rendered = self.render_template(template, filename, exiftool)
                finder_comment.extend(rendered)

        if comment := "\n".join(finder_comment):
            self.verbose(f"Writing Finder comment {comment} to {filename}")
            self.write_finder_comment(filename, comment)
            file_count = 1

        for xattr, template in self.xattr_template:
            rendered = self.render_template(template, filename, exiftool)
            file_count = (
                1
                if self.write_extended_attributes(filename, xattr, rendered)
                else file_count
            )

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

    def write_extended_attributes(self, filename, attr, value):
        """Write extended attributes to file"""
        if self.dry_run:
            return
        md = osxmetadata.OSXMetaData(filename)
        attr_name = MDITEM_ATTRIBUTE_SHORT_NAMES[attr]
        islist = MDITEM_ATTRIBUTE_DATA[attr_name]["python_type"].startswith("list")
        if value:
            value = sorted(value) if islist else ", ".join(value)
        file_value = md.get(attr_name)

        if file_value and islist:
            file_value = sorted(file_value)

        file_updated = False
        if (not file_value and not value) or file_value == value:
            # if both not set or both equal, nothing to do
            # get_attribute returns None if not set and value will be [] if not set so can't directly compare
            self.verbose(
                f"Skipping extended attribute {attr_name} for {filename}: nothing to do"
            )
        elif value:
            self.verbose(
                f"Writing extended attribute {attr_name}={value} to {filename}"
            )
            md.set(attr_name, value)
            file_updated = True
        else:
            self.verbose(
                f"Existing extended attribute {attr_name}={file_value} but new value is null; clearing {attr_name} from {filename}"
            )
            # value not set but there was already a value so remove it
            md.clear_attribute(attr_name)
            file_updated = True

        return file_updated

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
        try:
            rendered, _ = phototemplate.render(template, options)
            return rendered
        except ValueError as e:
            raise ValueError(
                f"Invalid template syntax for template '{template}': {e}"
            ) from e

    def render_template(self, template, filename, exiftool):
        """Render a template"""
        phototemplate = PhotoTemplate(filename)
        options = RenderOptions(tag=None, exiftool=exiftool, filepath=filename)
        try:
            rendered, _ = phototemplate.render(template, options)
            return rendered
        except ValueError as e:
            raise ValueError(
                f"Invalid template syntax for template '{template}': {e}"
            ) from e


def exif_values_to_list(value):
    """Convert a value returned by ExifTool to a list if it is not already and filter out bad data"""
    if isinstance(value, list):
        value = [v for v in value if not str(v).startswith("(Binary data ")]
        return [str(v) for v in value]
    elif not str(value).startswith("(Binary data "):
        return [str(value)]
