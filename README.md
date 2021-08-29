# exif2findertags
Read exif metadata from images with exiftool and write to MacOS Finder tags.  For example, you could use this with Final Cut Pro and its "Keywords from Finder Tags" import feature to allow Final Cut Pro to access EXIF metadata. This is similar to the commercial app evrX but in a free command line tool.

# Installation
I recommend you install `exif2findertags` with [pipx](https://github.com/pipxproject/pipx). If you use `pipx`, you will not need to create a virtual environment as `pipx` takes care of this. The easiest way to do this on a Mac is to use [homebrew](https://brew.sh/):

- Open `Terminal` (search for `Terminal` in Spotlight or look in `Applications/Utilities`)
- Install `homebrew` according to instructions at [https://brew.sh/](https://brew.sh/)
- Type the following into Terminal: `brew install pipx`
- Then type this: `pipx install git+https://github.com/RhetTbull/exif2findertags.git`
- Now you should be able to run `exif2findertags` by typing: `exif2findertags`

Once you've installed `exif2findertags` with pipx, to upgrade to the latest version:

    pipx upgrade exif2findertags

`exif2findertags` uses [exiftool](https://exiftool.org) to extract metadata from photos and videos so you'll need to install exiftool.  `exif2findertags` will look in the path for exiftool.  Alternatively, you can specify the path to exiftool using the `--exiftool-path` option.  Because it uses exiftool, `exif2findertags` can read any metadata which exiftool is able to read.


# Usage
```
exif2findertags
Usage: python -m exif2findertags [OPTIONS] [FILES]...

  Create Finder tags from EXIF and other metadata in media files.

Specify which metadata tags to export to Finder tags: [at least 1 required]
  --tag TAG             Photo metadata tags to use as Finder tags; multiple tags
                        may be specified by repeating --tag, for example: `--tag
                        Keywords --tag ISO`.
  --tag-value TAG       Photo metadata tags to use as Finder tags; use only tag
                        value as keyword; multiple tags may be specified by
                        repeating --tag-value, for example: `--tag-value
                        Keywords --tag-value PersonInImage`.
  --all-tags            Include all metadata found in file as Finder tags; see
                        also, --group, --value.
  --tag-group GROUP     Include all metadata from GROUP tag group, e.g. '--tag-
                        group EXIF', '--tag-group XMP'; see also, --group,
                        --value.

Options for use with --all-tags or --tag-group: [mutually exclusive]
  -G, --group           Include tag group in Finder tag (for example,
                        'EXIF:Make' instead of 'Make') when used with --all-
                        tags.
  --value               Use only tag value (not tag name) as Finder tag when
                        used with --all-tags.

Settings:
  -V, --verbose         Show verbose output.
  --walk                Recursively walk directories.
  --exiftool-path PATH  Optional path to exiftool executable (will look in $PATH
                        if not specified).

Other options:
  --help                Show this message and exit.

Tag names used with --tag and --tag-value may be any tag that exiftool can read.
For a complete list of tag values, see https://exiftool.org/TagNames/. Tag names
may be specified with or without the tag group name.  For example: `--tag
Keywords` and `--tag IPTC:Keywords` are both valid. If specified, the group name
will be output to the name of the Finder tag when used with --tag. For example,
`--tag IPTC:Keywords` will result in a Finder tag named `IPTC:Keywords: Travel`
if `Travel` was one of the keywords and `--tag Keywords` would result in a
Finder tag of `Keywords: Travel`. To use only the tag value as the keyword, use
`--tag-value Keywords`, which would result in a Finder tag named `Travel`.

When used with --tag, Finder tags will be created in format `TagName: TagValue`.
For example, `--tag ISO` would produce something like `ISO: 100`.

exiftool must be installed as it is used to read the metadata from media files.
See https://exiftool.org/ to download and install exiftool.
```

You must specify one or more tag names using `-tag` or `--tag-value`.  Tag names must be valid names as specified in the exiftool [documentation](https://exiftool.org/TagNames/).  The group name may be omitted or included in same format as exfitool uses.

For example:

- `--tag Keywords` or `-tag IPTC:Keywords`
- `--tag-value PersonInImage` or `--tag-value XMP:PersonInImage`

`--tag TAGNAME` will produce a Finder tag named: "TAGNAME: Value" in the same format as the tag name was specified (e.g. with or without group name).  For exmaple:

- `Keywords: Travel` or `IPTC:Keywords: Travel`

`--tag-value` will produce a Finder tag named with just the value of the specified tag without the tag name.  For example:

- `Jane Smith` instead of `PersonInImage: Jane Smith`

# Roadmap

This is a new project under active development. Features in work:

- [x] --all-tags to output all tags without having to specify them
- [X] --tag-group GROUP to output all tags in a certain group, e.g. --tag-group EXIF
- [ ] Ability to also set the Finder comment field based on tag values, (for example, image description)
- [ ] Ability to use a config file to specify which tags to export
- [ ] Ability to specify tag format to use when creating new Finder tags
- [ ] Tests
- [ ] --overwrite to overwrite existing Finder tags

# Contributing

Feedback and contributions of all kinds welcome!  Please open an [issue](https://github.com/RhetTbull/exif2findertags/issues) if you would like to suggest enhancements or bug fixes.
