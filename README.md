# exif2findertags
Read exif metadata from images with exiftool and write to MacOS Finder tags

# Installation
I recommend you install `exif2findertags` with [pipx](https://github.com/pipxproject/pipx). If you use `pipx`, you will not need to create a virtual environment as `pipx` takes care of this. The easiest way to do this on a Mac is to use [homebrew](https://brew.sh/):

- Open `Terminal` (search for `Terminal` in Spotlight or look in `Applications/Utilities`)
- Install `homebrew` according to instructions at [https://brew.sh/](https://brew.sh/)
- Type the following into Terminal: `brew install pipx`
- Then type this: `pipx install git+https://github.com/RhetTbull/exif2findertags.git`
- Now you should be able to run `exif2findertags` by typing: `exif2findertags`

Once you've installed `exif2findertags` with pipx, to upgrade to the latest version:

    pipx upgrade exif2findertags


# Usage
```
exif2findertags
Usage:  [OPTIONS] [FILES]...

  CLI interface

Options:
  -V, --verbose         Show verbose output
  --tag TEXT            Photo metadata tags to use as Finder tags
  --tag-value TEXT      Photo metadata tags to use as Finder tags; use only
                        tag value as keyword
  --walk                Recursively walk directories
  --exiftool-path PATH  Optional path to exiftool executable (will look in
                        $PATH if not specified)
  --help                Show this message and exit.
```