# exif2findertags
Read exif metadata from images with exiftool and write to MacOS Finder tags

# Usage
```
Usage: exif2findertags [OPTIONS] [FILES]...

  CLI interface

Options:
  -V, --verbose         Show verbose output
  --tag TEXT            Photo metadata tags to use as Finder tags
  --tag-value TEXT      Photo metadata tags to use as Finder tags; use only
                        tag value as keyword
  --walk TEXT           Recursively walk directories
  --exiftool-path PATH  Path to exiftool executable
  --help                Show this message and exit.
```