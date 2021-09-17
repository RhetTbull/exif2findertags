""" Custom template system for osxphotos, implements osxphotos template language (OTL) """

import datetime

# import json
import locale

# import os
import pathlib
import shlex

# import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from textx import TextXSyntaxError, metamodel_from_file

from ._version import __version__
from .datetime_formatter import DateTimeFormatter
from .exiftool import ExifTool, ExifToolCaching
from .path_utils import sanitize_dirname, sanitize_filename, sanitize_pathpart
from .text_detection import detect_text

# from .text_detection import detect_text
# from .utils import expand_and_validate_filepath, load_function

# ensure locale set to user's locale
locale.setlocale(locale.LC_ALL, "")

OTL_GRAMMAR_MODEL = str(pathlib.Path(__file__).parent / "phototemplate.tx")
"""TextX metamodel for osxphotos template language """

NONE_STR_SENTINEL = "__XYZZY_PHOTO_TEMPLATE_NONE_XYZZY__"

TEXT_DETECTION_CONFIDENCE_THRESHOLD = 0.7

DATETIME_SUBFIELDS = [
    "date",
    "year",
    "yy",
    "mm",
    "month",
    "mon",
    "dd",
    "dow",
    "doy",
    "hour",
    "min",
    "sec",
    "strftime",
]

# Permitted substitutions (each of these returns a single value or None)
TEMPLATE_SUBSTITUTIONS = {
    "{created}": "Photo's creation date if set in the EXIF data, otherwise null; ISO 8601 format",
    "{created.date}": "Photo's creation date in ISO format, e.g. '2020-03-22'",
    "{created.year}": "4-digit year of photo creation time",
    "{created.yy}": "2-digit year of photo creation time",
    "{created.mm}": "2-digit month of the photo creation time (zero padded)",
    "{created.month}": "Month name in user's locale of the photo creation time",
    "{created.mon}": "Month abbreviation in the user's locale of the photo creation time",
    "{created.dd}": "2-digit day of the month (zero padded) of photo creation time",
    "{created.dow}": "Day of week in user's locale of the photo creation time",
    "{created.doy}": "3-digit day of year (e.g Julian day) of photo creation time, starting from 1 (zero padded)",
    "{created.hour}": "2-digit hour of the photo creation time",
    "{created.min}": "2-digit minute of the photo creation time",
    "{created.sec}": "2-digit second of the photo creation time",
    "{created.strftime}": "Apply strftime template to file creation date/time. Should be used in form "
    + "{created.strftime,TEMPLATE} where TEMPLATE is a valid strftime template, e.g. "
    + "{created.strftime,%Y-%U} would result in year-week number of year: '2020-23'. "
    + "If used with no template will return null value. "
    + "See https://strftime.org/ for help on strftime templates.",
    "{modified}": "Photo's modification date if set in the EXIF data, otherwise null; ISO 8601 format",
    "{modified.date}": "Photo's modification date in ISO format, e.g. '2020-03-22'; uses creation date if photo is not modified",
    "{modified.year}": "4-digit year of photo modification time; uses creation date if photo is not modified",
    "{modified.yy}": "2-digit year of photo modification time; uses creation date if photo is not modified",
    "{modified.mm}": "2-digit month of the photo modification time (zero padded); uses creation date if photo is not modified",
    "{modified.month}": "Month name in user's locale of the photo modification time; uses creation date if photo is not modified",
    "{modified.mon}": "Month abbreviation in the user's locale of the photo modification time; uses creation date if photo is not modified",
    "{modified.dd}": "2-digit day of the month (zero padded) of the photo modification time; uses creation date if photo is not modified",
    "{modified.dow}": "Day of week in user's locale of the photo modification time; uses creation date if photo is not modified",
    "{modified.doy}": "3-digit day of year (e.g Julian day) of photo modification time, starting from 1 (zero padded); uses creation date if photo is not modified",
    "{modified.hour}": "2-digit hour of the photo modification time; uses creation date if photo is not modified",
    "{modified.min}": "2-digit minute of the photo modification time; uses creation date if photo is not modified",
    "{modified.sec}": "2-digit second of the photo modification time; uses creation date if photo is not modified",
    "{modified.strftime}": "Apply strftime template to file modification date/time. Should be used in form "
    + "{modified.strftime,TEMPLATE} where TEMPLATE is a valid strftime template, e.g. "
    + "{modified.strftime,%Y-%U} would result in year-week number of year: '2020-23'. "
    + "If used with no template will return null value. Uses creation date if photo is not modified. "
    + "See https://strftime.org/ for help on strftime templates.",
    "{today.date}": "Current date in iso format, e.g. '2020-03-22'",
    "{today.year}": "4-digit year of current date",
    "{today.yy}": "2-digit year of current date",
    "{today.mm}": "2-digit month of the current date (zero padded)",
    "{today.month}": "Month name in user's locale of the current date",
    "{today.mon}": "Month abbreviation in the user's locale of the current date",
    "{today.dd}": "2-digit day of the month (zero padded) of current date",
    "{today.dow}": "Day of week in user's locale of the current date",
    "{today.doy}": "3-digit day of year (e.g Julian day) of current date, starting from 1 (zero padded)",
    "{today.hour}": "2-digit hour of the current date",
    "{today.min}": "2-digit minute of the current date",
    "{today.sec}": "2-digit second of the current date",
    "{today.strftime}": "Apply strftime template to current date/time. Should be used in form "
    + "{today.strftime,TEMPLATE} where TEMPLATE is a valid strftime template, e.g. "
    + "{today.strftime,%Y-%U} would result in year-week number of year: '2020-23'. "
    + "If used with no template will return null value. "
    + "See https://strftime.org/ for help on strftime templates.",
    "{comma}": "A comma: ','",
    "{semicolon}": "A semicolon: ';'",
    "{questionmark}": "A question mark: '?'",
    "{pipe}": "A vertical pipe: '|'",
    "{openbrace}": "An open brace: '{'",
    "{closebrace}": "A close brace: '}'",
    "{openparens}": "An open parentheses: '('",
    "{closeparens}": "A close parentheses: ')'",
    "{openbracket}": "An open bracket: '['",
    "{closebracket}": "A close bracket: ']'",
    "{newline}": r"A newline: '\n'",
    "{lf}": r"A line feed: '\n', alias for {newline}",
    "{cr}": r"A carriage return: '\r'",
    "{crlf}": r"a carriage return + line feed: '\r\n'",
    # "{osxphotos_version}": f"The osxphotos version, e.g. '{__version__}'",
    # "{osxphotos_cmd_line}": "The full command line used to run osxphotos",
}

TEMPLATE_SUBSTITUTIONS_PATHLIB = {
    # "{export_dir}": "The full path to the export directory",
    "{filepath}": "The full path to the file being processed.",
}

# Permitted multi-value substitutions (each of these returns None or 1 or more values)
TEMPLATE_SUBSTITUTIONS_MULTI_VALUED = {
    "{GROUP}": "The tag group (as defined by exiftool) for the tag being processed, for example, 'EXIF'; for use with --tag-format.",
    "{TAG}": "The name of the tag being processed, for example, 'ImageDescription'; for use with --tag-format.",
    "{VALUE}": "The value of the tag being processed, for example, 'My Image Description'; for use with --tag-format.",
    # "{shell_quote}": "Use in form '{shell_quote,TEMPLATE}'; quotes the rendered TEMPLATE value(s) for safe usage in the shell, e.g. My file.jpeg => 'My file.jpeg'; only adds quotes if needed.",
    "{strip}": "Use in form '{strip,TEMPLATE}'; strips whitespace from begining and end of rendered TEMPLATE value(s).",
    # "{function}": "Execute a python function from an external file and use return value as template substitution. "
    # + "Use in format: {function:file.py::function_name} where 'file.py' is the name of the python file and 'function_name' is the name of the function to call. "
    # + "The function will be passed the PhotoInfo object for the photo. "
    # + "See https://github.com/RhetTbull/osxphotos/blob/master/examples/template_function.py for an example of how to implement a template function.",
    "{detected_text}": "List of text strings found in the image after performing text detection. "
    + "You may pass a confidence threshold value between 0.0 and 1.0 after a colon as in '{detected_text:0.5}'; "
    + f"The default confidence threshold is {TEXT_DETECTION_CONFIDENCE_THRESHOLD}. "
    + "'{detected_text}' works only on macOS Catalina (10.15) or later.",
}

TEMPLATE_SUBSTITUTIONS_EXIFTOOL = {
    "{Group:Tag}": "Any valid exiftool tag with optional group name, e.g. '{EXIF:Make}', '{Make}', '{IPTC:Keywords}', '{ISO}'; invalid or missing tags will be ignored."
}

TEMPLATE_SUBSTITUTIONS_ALL = {
    **TEMPLATE_SUBSTITUTIONS_EXIFTOOL,
    **TEMPLATE_SUBSTITUTIONS_MULTI_VALUED,
    **TEMPLATE_SUBSTITUTIONS_PATHLIB,
    **TEMPLATE_SUBSTITUTIONS,
}

FILTER_VALUES = {
    "lower": "Convert value to lower case, e.g. 'Value' => 'value'.",
    "upper": "Convert value to upper case, e.g. 'Value' => 'VALUE'.",
    "strip": "Strip whitespace from beginning/end of value, e.g. ' Value ' => 'Value'.",
    "titlecase": "Convert value to title case, e.g. 'my value' => 'My Value'.",
    "capitalize": "Capitalize first word of value and convert other words to lower case, e.g. 'MY VALUE' => 'My value'.",
    "braces": "Enclose value in curly braces, e.g. 'value => '{value}'.",
    "parens": "Enclose value in parentheses, e.g. 'value' => '(value')",
    "brackets": "Enclose value in brackets, e.g. 'value' => '[value]'",
    # "shell_quote": "Quotes the value for safe usage in the shell, e.g. My file.jpeg => 'My file.jpeg'; only adds quotes if needed.",
    # "function": "Run custom python function to filter value; use in format 'function:/path/to/file.py::function_name'. See example at https://github.com/RhetTbull/osxphotos/blob/master/examples/template_filter.py",
}

# Just the substitutions without the braces
SINGLE_VALUE_SUBSTITUTIONS = [
    field.replace("{", "").replace("}", "") for field in TEMPLATE_SUBSTITUTIONS
]

PATHLIB_SUBSTITUTIONS = [
    field.replace("{", "").replace("}", "") for field in TEMPLATE_SUBSTITUTIONS_PATHLIB
]

MULTI_VALUE_SUBSTITUTIONS = [
    field.replace("{", "").replace("}", "")
    for field in TEMPLATE_SUBSTITUTIONS_MULTI_VALUED
]

FIELD_NAMES = (
    SINGLE_VALUE_SUBSTITUTIONS + MULTI_VALUE_SUBSTITUTIONS + PATHLIB_SUBSTITUTIONS
)

# default values for string manipulation template options
INPLACE_DEFAULT = ","
# PATH_SEP_DEFAULT = os.path.sep

PUNCTUATION = {
    "comma": ",",
    "semicolon": ";",
    "pipe": "|",
    "openbrace": "{",
    "closebrace": "}",
    "openparens": "(",
    "closeparens": ")",
    "openbracket": "[",
    "closebracket": "]",
    "questionmark": "?",
    "newline": "\n",
    "lf": "\n",
    "cr": "\r",
    "crlf": "\r\n",
}


@dataclass
class RenderOptions:
    """Options for PhotoTemplate.render

    tag: tag name being processed
    none_str: str to use default for None values
    path_sep: optional string to use as path separator, default is os.path.sep
    expand_inplace: expand multi-valued substitutions in-place as a single string
        instead of returning individual strings
    inplace_sep: optional string to use as separator between multi-valued keywords
    with expand_inplace; default is ','
    filename: if True, template output will be sanitized to produce valid file name
    dirname: if True, template output will be sanitized to produce valid directory name
    strip: if True, strips leading/trailing whitespace from rendered templates
    export_dir: set to the export directory if you want to evalute {export_dir} template
    dest_path: set to the destination path of the photo (for use by {function} template), only valid with --filename
    filepath: set to value for filepath of the photo being processed if you want to evaluate {filepath} template
    quote: quote path templates for execution in the shell
    exiftool: an ExifToolCaching instance
    """

    tag: Optional[str] = None
    none_str: str = NONE_STR_SENTINEL
    expand_inplace: bool = False
    inplace_sep: Optional[str] = INPLACE_DEFAULT
    filename: bool = False
    dirname: bool = False
    strip: bool = False
    export_dir: Optional[str] = None
    dest_path: Optional[str] = None
    filepath: Optional[str] = None
    quote: bool = False
    exiftool: Optional[ExifTool] = None


class PhotoTemplateParser:
    """Parser for PhotoTemplate"""

    # implemented as Singleton

    def __new__(cls, *args, **kwargs):
        """create new object or return instance of already created singleton"""
        if not hasattr(cls, "instance") or not cls.instance:
            cls.instance = super().__new__(cls)

        return cls.instance

    def __init__(self):
        """return existing singleton or create a new one"""

        if hasattr(self, "metamodel"):
            return

        self.metamodel = metamodel_from_file(OTL_GRAMMAR_MODEL, skipws=False)

    def parse(self, template_statement):
        """Parse a template_statement string"""
        return self.metamodel.model_from_str(template_statement)

    def fields(self, template_statement):
        """Return list of fields found in a template statement; does not verify that fields are valid"""
        model = self.parse(template_statement)
        return [ts.template.field for ts in model.template_strings if ts.template]


class PhotoTemplate:
    """PhotoTemplate class to render a template string from a PhotoInfo object"""

    def __init__(self, photopath: str, exiftool_path: Optional[str] = None):
        """Inits PhotoTemplate class with photo

        Args:
            photo: a PhotoInfo instance.
            exiftool_path: optional path to exiftool for use with {exiftool:} template; if not provided, will look for exiftool in $PATH
        """
        if not pathlib.Path(photopath).exists():
            raise FileNotFoundError(f"Photo path {photopath} does not exist")
        if exiftool_path and not pathlib.Path(exiftool_path).exists():
            raise FileNotFoundError(f"Exiftool path {exiftool_path} does not exist")

        self.photopath = photopath
        self.exiftool_path = exiftool_path

        # holds value of current date/time for {today.x} fields
        # gets initialized in get_template_value
        self.today = None

        # get parser singleton
        self.parser = PhotoTemplateParser()

        # initialize render options
        # this will be done in render() but for testing, some of the lookup functions are called directly
        options = RenderOptions()
        self.options = options
        self.tag = options.tag
        self.group, self.tagname = "", ""
        self.inplace_sep = options.inplace_sep
        self.none_str = options.none_str
        self.expand_inplace = options.expand_inplace
        self.filename = options.filename
        self.dirname = options.dirname
        self.strip = options.strip
        self.export_dir = options.export_dir
        self.filepath = options.filepath
        self.quote = options.quote
        self.dest_path = options.dest_path
        self.exiftool = options.exiftool or ExifToolCaching(
            self.photopath, exiftool=self.exiftool_path
        )

    def render(
        self,
        template: str,
        options: RenderOptions,
    ):
        """Render a filename or directory template

        Args:
            template: str template
            options: a RenderOptions instance

        Returns:
            ([rendered_strings], [unmatched]): tuple of list of rendered strings and list of unmatched template values
        """

        if type(template) is not str:
            raise TypeError(f"template must be type str, not {type(template)}")

        self.options = options
        self.tag = options.tag
        self.group, self.tagname = split_group_tag(self.tag) if self.tag else ("", "")
        self.inplace_sep = options.inplace_sep
        self.none_str = options.none_str
        self.expand_inplace = options.expand_inplace
        self.filename = options.filename
        self.dirname = options.dirname
        self.strip = options.strip
        self.export_dir = options.export_dir
        self.dest_path = options.dest_path
        self.filepath = options.filepath
        self.quote = options.quote
        self.dest_path = options.dest_path
        self.exiftool = options.exiftool or self.exiftool

        try:
            model = self.parser.parse(template)
        except TextXSyntaxError as e:
            raise ValueError(f"SyntaxError: {e}")

        if not model:
            # empty string
            return [], []

        rendered, unmatched = self._render_statement(model)
        rendered = [r for r in rendered if NONE_STR_SENTINEL not in r]
        return rendered, unmatched

    def _render_statement(
        self,
        statement,
    ):
        results = []
        unmatched = []
        for ts in statement.template_strings:
            results, unmatched = self._render_template_string(
                ts,
                results=results,
                unmatched=unmatched,
            )

        rendered_strings = results

        if self.filename:
            rendered_strings = [
                sanitize_filename(rendered_str) for rendered_str in rendered_strings
            ]

        if self.strip:
            rendered_strings = [
                rendered_str.strip() for rendered_str in rendered_strings
            ]

        return rendered_strings, unmatched

    def _render_template_string(
        self,
        ts,
        results=None,
        unmatched=None,
    ):
        """Render a TemplateString object"""

        results = results or [""]
        unmatched = unmatched or []

        if ts.template:
            # have a template field to process
            field = ts.template.field
            field_part = field.split(".")[0]
            # if field not in FIELD_NAMES and field_part not in FIELD_NAMES:
            #     unmatched.append(field)
            #     return [], unmatched

            subfield = ts.template.subfield

            # process filters
            filters = []
            if ts.template.filter is not None:
                filters = ts.template.filter.value

            # # process path_sep
            # if ts.template.pathsep is not None:
            #     path_sep = ts.template.pathsep.value

            # process delim
            if ts.template.delim is not None:
                # if value is None, means format was {+field}
                delim = ts.template.delim.value or ""
            else:
                delim = None

            if ts.template.bool is not None:
                is_bool = True
                if ts.template.bool.value is not None:
                    bool_val, u = self._render_statement(
                        ts.template.bool.value,
                    )
                    unmatched.extend(u)
                else:
                    # blank bool value
                    bool_val = [""]
            else:
                is_bool = False
                bool_val = None

            # process default
            if ts.template.default is not None:
                # default is also a TemplateString
                if ts.template.default.value is not None:
                    default, u = self._render_statement(
                        ts.template.default.value,
                    )
                    unmatched.extend(u)
                else:
                    # blank default value
                    default = [""]
            else:
                default = []

            # process conditional
            if ts.template.conditional is not None:
                operator = ts.template.conditional.operator
                negation = ts.template.conditional.negation
                if ts.template.conditional.value is not None:
                    # conditional value is also a TemplateString
                    conditional_value, u = self._render_statement(
                        ts.template.conditional.value,
                        # path_sep=path_sep,
                    )
                    unmatched.extend(u)
                else:
                    # this shouldn't happen
                    conditional_value = [""]
            else:
                operator = None
                negation = None
                conditional_value = []

            vals = []
            if (
                field in SINGLE_VALUE_SUBSTITUTIONS
                or field.split(".")[0] in SINGLE_VALUE_SUBSTITUTIONS
            ):
                vals = self.get_template_value(
                    field,
                    default=default,
                    subfield=subfield,
                    # delim=delim or self.inplace_sep,
                    # path_sep=path_sep,
                )
            # elif field == "function":
            #     if subfield is None:
            #         raise ValueError(
            #             "SyntaxError: filename and function must not be null with {function::filename.py:function_name}"
            #         )
            #     vals = self.get_template_value_function(
            #         subfield,
            #     )
            elif field in MULTI_VALUE_SUBSTITUTIONS:
                vals = self.get_template_value_multi(field, subfield, default=default)
            elif field.split(".")[0] in PATHLIB_SUBSTITUTIONS:
                vals = self.get_template_value_pathlib(field)
            else:
                # assume it's an exif field in form "tag" or "group:tag"
                exiftag = f"{field}:{subfield}" if subfield else f"{field}"
                vals = self.get_template_value_exiftool(tag=exiftag)

            vals = [val for val in vals if val is not None]

            if self.expand_inplace or delim is not None:
                sep = delim if delim is not None else self.inplace_sep
                vals = [sep.join(sorted(vals))] if vals else []

            for filter_ in filters:
                vals = self.get_template_value_filter(filter_, vals)

            # process find/replace
            if ts.template.findreplace:
                new_vals = []
                for val in vals:
                    for pair in ts.template.findreplace.pairs:
                        find = pair.find or ""
                        repl = pair.replace or ""
                        val = val.replace(find, repl)
                    new_vals.append(val)
                vals = new_vals

            if operator:
                # have a conditional operator

                def string_test(test_function):
                    """Perform string comparison using test_function; closure to capture conditional_value, vals, negation"""
                    match = False
                    for c in conditional_value:
                        for v in vals:
                            if test_function(v, c):
                                match = True
                                break
                        if match:
                            break
                    if (match and not negation) or (negation and not match):
                        return ["True"]
                    else:
                        return []

                def comparison_test(test_function):
                    """Perform numerical comparisons using test_function; closure to capture conditional_val, vals, negation"""
                    if len(vals) != 1 or len(conditional_value) != 1:
                        raise ValueError(
                            f"comparison operators may only be used with a single value: {vals} {conditional_value}"
                        )
                    try:
                        match = bool(
                            test_function(float(vals[0]), float(conditional_value[0]))
                        )
                        if (match and not negation) or (negation and not match):
                            return ["True"]
                        else:
                            return []
                    except ValueError as e:
                        raise ValueError(
                            f"comparison operators may only be used with values that can be converted to numbers: {vals} {conditional_value}"
                        )

                if operator in ["contains", "matches", "startswith", "endswith"]:
                    # process any "or" values separated by "|"
                    temp_values = []
                    for c in conditional_value:
                        temp_values.extend(c.split("|"))
                    conditional_value = temp_values

                if operator == "contains":
                    vals = string_test(lambda v, c: c in v)
                elif operator == "matches":
                    vals = string_test(lambda v, c: v == c)
                elif operator == "startswith":
                    vals = string_test(lambda v, c: v.startswith(c))
                elif operator == "endswith":
                    vals = string_test(lambda v, c: v.endswith(c))
                elif operator == "==":
                    match = sorted(vals) == sorted(conditional_value)
                    if (match and not negation) or (negation and not match):
                        vals = ["True"]
                    else:
                        vals = []
                elif operator == "!=":
                    match = sorted(vals) != sorted(conditional_value)
                    if (match and not negation) or (negation and not match):
                        vals = ["True"]
                    else:
                        vals = []
                elif operator == "<":
                    vals = comparison_test(lambda v, c: v < c)
                elif operator == "<=":
                    vals = comparison_test(lambda v, c: v <= c)
                elif operator == ">":
                    vals = comparison_test(lambda v, c: v > c)
                elif operator == ">=":
                    vals = comparison_test(lambda v, c: v >= c)

            if is_bool:
                vals = default if not vals else bool_val
            elif not vals:
                vals = default or [self.none_str]

            pre = ts.pre or ""
            post = ts.post or ""

            rendered = [pre + val + post for val in vals]
            results_new = []
            for ren in rendered:
                for res in results:
                    res_new = res + ren
                    results_new.append(res_new)
            results = results_new

        else:
            # no template
            pre = ts.pre or ""
            post = ts.post or ""
            results = [r + pre + post for r in results]

        return results, unmatched

    def get_template_value(
        self,
        field,
        default,
        subfield=None,
    ):
        """lookup value for template field (single-value template substitutions)

        Args:
            field: template field to find value for.
            default: the default value provided by the user
            subfield: subfield (value after : in field)

        Returns:
            The matching template value (which may be None).

        Raises:
            ValueError if no rule exists for field.
        """

        # initialize today with current date/time if needed
        if self.today is None:
            self.today = datetime.datetime.now()
        created = self.get_created_date()
        modified = self.get_modified_date()

        value = None

        # wouldn't a switch/case statement be nice...
        if field == "created":
            value = created.isoformat() if created else None
        elif field == "created.date":
            value = DateTimeFormatter(created).date if created else None
        elif field == "created.year":
            value = DateTimeFormatter(created).year if created else None
        elif field == "created.yy":
            value = DateTimeFormatter(created).yy if created else None
        elif field == "created.mm":
            value = DateTimeFormatter(created).mm if created else None
        elif field == "created.month":
            value = DateTimeFormatter(created).month if created else None
        elif field == "created.mon":
            value = DateTimeFormatter(created).mon if created else None
        elif field == "created.dd":
            value = DateTimeFormatter(created).dd if created else None
        elif field == "created.dow":
            value = DateTimeFormatter(created).dow if created else None
        elif field == "created.doy":
            value = DateTimeFormatter(created).doy if created else None
        elif field == "created.hour":
            value = DateTimeFormatter(created).hour if created else None
        elif field == "created.min":
            value = DateTimeFormatter(created).min if created else None
        elif field == "created.sec":
            value = DateTimeFormatter(created).sec if created else None
        elif field == "created.strftime":
            if default:
                try:
                    value = created.strftime(default[0]) if created else None
                except:
                    raise ValueError(f"Invalid strftime template: '{default}'")
            else:
                value = None
        elif field == "modified":
            value = modified.isoformat() if modified else None
        elif field == "modified.date":
            value = (
                DateTimeFormatter(modified).date
                if modified
                else DateTimeFormatter(modified).date
            )
        elif field == "modified.year":
            value = (
                DateTimeFormatter(modified).year
                if modified
                else DateTimeFormatter(modified).year
            )
        elif field == "modified.yy":
            value = (
                DateTimeFormatter(modified).yy
                if modified
                else DateTimeFormatter(modified).yy
            )
        elif field == "modified.mm":
            value = (
                DateTimeFormatter(modified).mm
                if modified
                else DateTimeFormatter(modified).mm
            )
        elif field == "modified.month":
            value = (
                DateTimeFormatter(modified).month
                if modified
                else DateTimeFormatter(modified).month
            )
        elif field == "modified.mon":
            value = (
                DateTimeFormatter(modified).mon
                if modified
                else DateTimeFormatter(modified).mon
            )
        elif field == "modified.dd":
            value = (
                DateTimeFormatter(modified).dd
                if modified
                else DateTimeFormatter(modified).dd
            )
        elif field == "modified.dow":
            value = (
                DateTimeFormatter(modified).dow
                if modified
                else DateTimeFormatter(modified).dow
            )
        elif field == "modified.doy":
            value = (
                DateTimeFormatter(modified).doy
                if modified
                else DateTimeFormatter(modified).doy
            )
        elif field == "modified.hour":
            value = (
                DateTimeFormatter(modified).hour
                if modified
                else DateTimeFormatter(modified).hour
            )
        elif field == "modified.min":
            value = (
                DateTimeFormatter(modified).min
                if modified
                else DateTimeFormatter(modified).min
            )
        elif field == "modified.sec":
            value = (
                DateTimeFormatter(modified).sec
                if modified
                else DateTimeFormatter(modified).sec
            )
        elif field == "modified.strftime":
            if default:
                try:
                    value = modified.strftime(default[0]) if modified else None
                except:
                    raise ValueError(f"Invalid strftime template: '{default}'")
            else:
                value = None
        elif field == "today.date":
            value = DateTimeFormatter(self.today).date
        elif field == "today.year":
            value = DateTimeFormatter(self.today).year
        elif field == "today.yy":
            value = DateTimeFormatter(self.today).yy
        elif field == "today.mm":
            value = DateTimeFormatter(self.today).mm
        elif field == "today.month":
            value = DateTimeFormatter(self.today).month
        elif field == "today.mon":
            value = DateTimeFormatter(self.today).mon
        elif field == "today.dd":
            value = DateTimeFormatter(self.today).dd
        elif field == "today.dow":
            value = DateTimeFormatter(self.today).dow
        elif field == "today.doy":
            value = DateTimeFormatter(self.today).doy
        elif field == "today.hour":
            value = DateTimeFormatter(self.today).hour
        elif field == "today.min":
            value = DateTimeFormatter(self.today).min
        elif field == "today.sec":
            value = DateTimeFormatter(self.today).sec
        elif field == "today.strftime":
            if default:
                try:
                    value = self.today.strftime(default[0])
                except:
                    raise ValueError(f"Invalid strftime template: '{default}'")
            else:
                value = None
        elif field in PUNCTUATION:
            value = PUNCTUATION[field]
        # elif field == "osxphotos_version":
        #     value = __version__
        # elif field == "osxphotos_cmd_line":
        # value = " ".join(sys.argv)
        else:
            # if here, didn't get a match
            raise ValueError(f"Unhandled template value: {field}")

        if self.filename:
            value = sanitize_pathpart(value)
        elif self.dirname:
            value = sanitize_dirname(value)

        # ensure no empty strings in value (see #512)
        value = None if value == "" else value

        return [value]

    def get_template_value_pathlib(self, field):
        """lookup value for template pathlib template fields

        Args:
            field: template field to find value for.

        Returns:
            The matching template value (which may be None).

        Raises:
            ValueError if no rule exists for field.
        """
        field_stem = field.split(".")[0]
        if field_stem not in PATHLIB_SUBSTITUTIONS:
            raise ValueError(f"SyntaxError: Unknown field: {field}")

        field_value = None
        try:
            field_value = getattr(self, field_stem)
        except AttributeError:
            raise ValueError(f"Unknown path-like field: {field_stem}")

        value = _get_pathlib_value(field, field_value, self.quote)

        if self.filename:
            value = sanitize_pathpart(value)
        elif self.dirname:
            value = sanitize_dirname(value)

        return [value]

    def get_template_value_filter(self, filter_, values):
        if filter_ == "lower":
            if values and type(values) == list:
                value = [v.lower() for v in values]
            else:
                value = [values.lower()] if values else []
        elif filter_ == "upper":
            if values and type(values) == list:
                value = [v.upper() for v in values]
            else:
                value = [values.upper()] if values else []
        elif filter_ == "strip":
            if values and type(values) == list:
                value = [v.strip() for v in values]
            else:
                value = [values.strip()] if values else []
        elif filter_ == "capitalize":
            if values and type(values) == list:
                value = [v.capitalize() for v in values]
            else:
                value = [values.capitalize()] if values else []
        elif filter_ == "titlecase":
            if values and type(values) == list:
                value = [v.title() for v in values]
            else:
                value = [values.title()] if values else []
        elif filter_ == "braces":
            if values and type(values) == list:
                value = ["{" + v + "}" for v in values]
            else:
                value = ["{" + values + "}"] if values else []
        elif filter_ == "parens":
            if values and type(values) == list:
                value = ["(" + v + ")" for v in values]
            else:
                value = ["(" + values + ")"] if values else []
        elif filter_ == "brackets":
            if values and type(values) == list:
                value = ["[" + v + "]" for v in values]
            else:
                value = ["[" + values + "]"] if values else []
        elif filter_ == "shell_quote":
            if values and type(values) == list:
                value = [shlex.quote(v) for v in values]
            else:
                value = [shlex.quote(values)] if values else []
        # elif filter_.startswith("function:"):
        # value = self.get_template_value_filter_function(filter_, values)
        else:
            raise ValueError(f"Unhandled filter: {filter_}")
        return value

    def get_template_value_multi(self, field, subfield, default):
        """lookup value for template field (multi-value template substitutions)

        Args:
            field: template field to find value for.
            subfield: the template subfield value
            default: value of default field

        Returns:
            List of the matching template values or [].

        Raises:
            ValueError if no rule exists for field.
        """

        """ return list of values for a multi-valued template field """

        values = []
        if field == "GROUP":
            values = [self.group]
        elif field == "TAG":
            values = [self.tagname]
        elif field == "VALUE":
            values = self.get_template_value_exiftool(self.tag)
        elif field == "shell_quote":
            values = [shlex.quote(v) for v in default if v]
        elif field == "strip":
            values = [v.strip() for v in default]
        elif field == "detected_text":
            exifdict = self.exiftool.asdict(tag_groups=False)
            orientation = exifdict.get("Orientation", None)
            values = _get_detected_text(
                self.photopath, orientation=orientation, confidence=subfield
            )
        else:
            raise ValueError(f"Unhandled template value: {field}")

        # sanitize directory names if needed, folder_album handled differently above
        if self.filename:
            values = [sanitize_pathpart(value) for value in values]
        elif self.dirname and field != "folder_album":
            # skip folder_album because it would have been handled above
            values = [sanitize_dirname(value) for value in values]

        # If no values, insert None so code below will substitute none_str for None
        values = values or []
        return values

    def get_template_value_exiftool(
        self,
        tag,
        default=None,
    ):
        """Get template value for format "{EXIF:Model}" """

        exifdict = self.exiftool.asdict(normalized=True)
        exifdict_no_groups = self.exiftool.asdict(tag_groups=False, normalized=True)
        exifdict = exifdict.copy()
        exifdict.update(exifdict_no_groups)

        tag = tag.lower()
        tag_subfield = None
        if "." in tag:
            tag, tag_subfield = tag.split(".")

        values = []
        if tag in exifdict:
            values = exifdict[tag]
            values = [values] if not isinstance(values, list) else values
            values = [str(v) for v in values]

            # "(Binary data " below is hack workaround for "(Binary data 0 bytes, use -b option to extract)" error that happens
            # when exporting video with keywords on Photos 5.0 / Catalina
            values = [v for v in values if not v.startswith("(Binary data ")]

            if tag_subfield:
                # handle datetime formatting
                if tag_subfield not in DATETIME_SUBFIELDS:
                    raise ValueError(
                        f"Invalid value {tag_subfield} for date/time formatter"
                    )

                values = [
                    getattr(
                        DateTimeFormatter(datetime.datetime.fromisoformat(v)),
                        tag_subfield,
                    )
                    for v in values
                ]

            # sanitize directory names if needed
            if self.filename:
                values = [sanitize_pathpart(value) for value in values]
            elif self.dirname:
                values = [sanitize_dirname(value) for value in values]

        return values

    def get_created_date(self):
        """Get created date from EXIF data or None"""

        data = self.exiftool.asdict()
        for tag in [
            "Composite:SubSecDateTimeOriginal",
            "Composite:DateTimeCreated",
            "QuickTime:CreationDate",
            "QuickTime:CreateDate",
            "EXIF:DateTimeOriginal",
            "EXIF:CreateDate",
            "IPTC:DateCreated",
        ]:
            if tag in data:
                return exiftool_date_to_datetime(data[tag])
        else:
            return None

    def get_modified_date(self):
        """Get modified date from EXIF data or None"""

        data = self.exiftool.asdict()
        for tag in [
            "Composite:SubSecModifyDate",
            "EXIF:ModifyDate",
            "QuickTime:ModifyDate",
        ]:
            if tag in data:
                return exiftool_date_to_datetime(data[tag])
        else:
            return None

    # def get_template_value_function(
    #     self,
    #     subfield,
    # ):
    #     """Get template value from external function"""

    #     if "::" not in subfield:
    #         raise ValueError(
    #             f"SyntaxError: could not parse function name from '{subfield}'"
    #         )

    #     filename, funcname = subfield.split("::")

    #     filename_validated = expand_and_validate_filepath(filename)
    #     if not filename_validated:
    #         raise ValueError(f"'{filename}' does not appear to be a file")

    #     template_func = load_function(filename_validated, funcname)
    #     values = template_func(self.photo, options=self.options)

    #     if not isinstance(values, (str, list)):
    #         raise TypeError(
    #             f"Invalid return type for function {funcname}: expected str or list"
    #         )
    #     if type(values) == str:
    #         values = [values]

    #     # sanitize directory names if needed
    #     if self.filename:
    #         values = [sanitize_pathpart(value) for value in values]
    #     elif self.dirname:
    #         # sanitize but don't replace any "/" as user function may want to create sub directories
    #         values = [sanitize_dirname(value, replacement=None) for value in values]

    #     return values

    # def get_template_value_filter_function(self, filter_, values):
    #     """Filter template value from external function"""

    #     filter_ = filter_.replace("function:", "")

    #     if "::" not in filter_:
    #         raise ValueError(
    #             f"SyntaxError: could not parse function name from '{filter_}'"
    #         )

    #     filename, funcname = filter_.split("::")

    #     filename_validated = expand_and_validate_filepath(filename)
    #     if not filename_validated:
    #         raise ValueError(f"'{filename}' does not appear to be a file")

    #     template_func = load_function(filename_validated, funcname)

    #     if not isinstance(values, (list, tuple)):
    #         values = [values]
    #     values = template_func(values)

    #     if not isinstance(values, list):
    #         raise TypeError(
    #             f"Invalid return type for function {funcname}: expected list"
    #         )

    #     return values

    # def get_photo_video_type(self, default):
    #     """return media type, e.g. photo or video"""
    #     default_dict = parse_default_kv(default, PHOTO_VIDEO_TYPE_DEFAULTS)
    #     if self.photo.isphoto:
    #         return default_dict["photo"]
    #     else:
    #         return default_dict["video"]

    # def get_media_type(self, default):
    #     """return special media type, e.g. slow_mo, panorama, etc., defaults to photo or video if no special type"""
    #     default_dict = parse_default_kv(default, MEDIA_TYPE_DEFAULTS)
    #     p = self.photo
    #     if p.selfie:
    #         return default_dict["selfie"]
    #     elif p.time_lapse:
    #         return default_dict["time_lapse"]
    #     elif p.panorama:
    #         return default_dict["panorama"]
    #     elif p.slow_mo:
    #         return default_dict["slow_mo"]
    #     elif p.screenshot:
    #         return default_dict["screenshot"]
    #     elif p.portrait:
    #         return default_dict["portrait"]
    #     elif p.live_photo:
    #         return default_dict["live_photo"]
    #     elif p.burst:
    #         return default_dict["burst"]
    #     elif p.ismovie:
    #         return default_dict["video"]
    #     else:
    #         return default_dict["photo"]

    # def get_photo_bool_attribute(self, attr, default, bool_val):
    #     # get value for a PhotoInfo bool attribute
    #     val = getattr(self.photo, attr)
    #     if val:
    #         return bool_val
    #     else:
    #         return default


def split_group_tag(exiftag: str) -> Tuple[str, str]:
    """split the group and tag from an exiftool tag in format Group:Tag or Tag"""
    if ":" not in exiftag:
        return "", exiftag

    group, tag = exiftag.split(":", 1)
    return group, tag


def parse_default_kv(default, default_dict):
    """parse a string in form key1=value1;key2=value2,... as used for some template fields

    Args:
        default: str, in form 'photo=foto;video=vidéo'
        default_dict: dict, in form {"photo": "fotos", "video": "vidéos"} with default values

    Returns:
        dict in form {"photo": "fotos", "video": "vidéos"}
    """

    default_dict_ = default_dict.copy()
    if default:
        defaults = default[0].split(";")
        for kv in defaults:
            try:
                k, v = kv.split("=")
                k = k.strip()
                v = v.strip()
                default_dict_[k] = v
            except ValueError:
                pass
    return default_dict_


def get_template_help():
    """Return help for template system as markdown string"""
    # TODO: would be better to use importlib.abc.ResourceReader but I can't find a single example of how to do this
    help_file = pathlib.Path(__file__).parent / "phototemplate.md"
    with open(help_file, "r") as fd:
        md = fd.read()
    return md


def _get_pathlib_value(field, value, quote):
    """Get the value for a pathlib.Path type template

    Args:
        field: the path field, e.g. "filename.stem"
        value: the value for the path component
        quote: bool; if true, quotes the returned path for safe execution in the shell
    """
    parts = field.split(".")

    if len(parts) == 1:
        return shlex.quote(value) if quote else value

    if len(parts) > 2:
        raise ValueError(f"Illegal value for path template: {field}")

    path = parts[0]
    attribute = parts[1]
    path = pathlib.Path(value)
    try:
        val = getattr(path, attribute)
        val_str = str(val)
        if quote:
            val_str = shlex.quote(val_str)
        return val_str
    except AttributeError:
        raise ValueError("Illegal value for path template: {attribute}")


def format_str_value(value, format_str):
    """Format value based on format code in field in format id:02d"""
    if not format_str:
        return str(value)
    format_str = "{0:" + f"{format_str}" + "}"
    return format_str.format(value)


def exiftool_date_to_datetime(date: str) -> datetime.datetime:
    """Convert EXIF date to datetime.datetime"""

    """ exiftool can produce date/times in a variety of formats:
        with TZ offset: "2021:08:01 21:51:33-07:00",
        no TZ offset: "2019:07:27 17:33:28",
        no time: "2019:04:15",
        subsecond, no TZ offset: "2019:04:15 14:40:24.86",
        subsecond, TZ offset: "2019:04:15 14:40:24.86-04:00",
  """

    date_time_formats = [
        "%Y:%m:%d %H:%M:%S%z",
        "%Y:%m:%d %H:%M:%S",
        "%Y:%m:%d %H:%M:%S.%f",
        "%Y:%m:%d %H:%M:%S.%f%z",
        "%Y:%m:%d",
    ]

    for dt_format in date_time_formats:
        try:
            parsed_date = datetime.datetime.strptime(date, dt_format)
        except ValueError as e:
            pass
        else:
            return parsed_date
    else:
        raise ValueError(
            f"Could not parse date format: {date} does not match {date_time_formats}"
        )


def _get_detected_text(
    photo_path: Union[str, pathlib.Path],
    orientation: Optional[int] = None,
    confidence: Optional[int] = TEXT_DETECTION_CONFIDENCE_THRESHOLD,
) -> List:
    """Returns the detected text for a photo"""

    photo_path = str(photo_path)

    confidence = (
        float(confidence)
        if confidence is not None
        else TEXT_DETECTION_CONFIDENCE_THRESHOLD
    )

    return [
        text
        for text, conf in detect_text(photo_path, orientation)
        if conf >= confidence
    ]
