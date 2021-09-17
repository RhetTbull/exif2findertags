# exif2findertags
Read exif metadata from images with [exiftool](https://exiftool.org/) and write to MacOS Finder tags and/or Finder comments.  For example, you could use this with Final Cut Pro and its "Keywords from Finder Tags" import feature to allow Final Cut Pro to access EXIF metadata. This is similar to the commercial app evrX but in a free command line tool. exif2findertags makes your photo & video metadata easier to work with and makes it easier to find the right image with Spotlight.  Works on macOS only.

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
$ exif2findertags --help
Usage: exif2findertags [OPTIONS] [FILES]...

  Create Finder tags and/or Finder comments from EXIF and other metadata in
  media files.

Specify which metadata tags to export to Finder tags and/or comments:
  [at least 1 required]
  --tag TAG                Photo metadata tags to use as Finder tags; multiple
                           tags may be specified by repeating --tag, for
                           example: `--tag Keywords --tag ISO`. Finder tags
                           will be in form 'TAG: VALUE', e.g. 'ISO: 80' or
                           'IPTC:Keywords: Travel'. If the group name is
                           specified it will be included in the Finder tag
                           name, otherwise, just the tag name will be included.
  --tag-value TAG          Photo metadata tags to use as Finder tags; use only
                           tag value as keyword; multiple tags may be specified
                           by repeating --tag-value, for example: `--tag-value
                           Keywords --tag-value PersonInImage`.
  --all-tags               Include all metadata found in file as Finder tags;
                           see also, --group, --value.
  --tag-group GROUP        Include all metadata from GROUP tag group, e.g. '--
                           tag-group EXIF', '--tag-group XMP'; see also,
                           --group, --value.
  --tag-match PATTERN      Include all metadata tags whose tag name matches
                           PATTERN, e.g. '--tag-match Exposure'; see also,
                           --group, --value. PATTERN is case-sensitive, e.g. '
                           --tag-match Exposure' matches EXIF:ExposureTime,
                           EXIF:ExposureMode, etc. but '--tag-match exposure'
                           would not; see also, --group, --value
  --fc TAG                 Photo metadata tags to use as Finder comments;
                           multiple tags may be specified by repeating --fc,
                           for example: `--fc Keywords --fc ISO`. Tags will be
                           appended to Finder comment. If the group name is
                           specified it will be included in the Finder comment,
                           otherwise, just the tag name will be included.
  --fc-value TAG           Photo metadata tags to use as Finder comments; use
                           only tag value as comment; multiple tags may be
                           specified by repeating --fc-value, for example:
                           `--fc-value Keywords --fc-value PersonInImage`. Tag
                           values will be appended to Finder comment.
  --tag-template TEMPLATE  Specify a custom template for Finder tag.  Multiple
                           templates may be specified by repeating '--tag-
                           template TEMPLATE'. For example, '--tag-template
                           "Camera: {Make|titlecase}{comma} {Model|titlecase}"'
                           would result in a tag of 'Camera: Nikon Corporation,
                           Nikon D810' if 'EXIF:Make=NIKON CORPORATION' and
                           'EXIF:Model=NIKON D810'. See Template System for
                           additional details.
  --fc-template TEMPLATE   Specify a custom template for Finder comments.
                           Multiple templates may be specified by repeating '--
                           fc-template TEMPLATE'. For example, '--fc-template
                           "Camera: {Make|titlecase}{comma} {Model|titlecase}"'
                           would result in a Finder comment of 'Camera: Nikon
                           Corporation, Nikon D810' if 'EXIF:Make=NIKON
                           CORPORATION' and 'EXIF:Model=NIKON D810'. See
                           Template System for additional details.
  --xattr-template ATTRIBUTE TEMPLATE
                           Set extended attribute ATTRIBUTE to TEMPLATE value.
                           Valid attributes are: 'authors', 'comment',
                           'copyright', 'creator', 'description',
                           'findercomment', 'headline', 'keywords',
                           'participants', 'projects', 'rating', 'subject',
                           'title', 'version'. For example, to set Spotlight
                           comment (distinct from Finder comment) to the
                           photo's title and description: '--xattr-template
                           comment "{Title}{newline}{ImageDescription}" '--
                           xattr-template' will overwrite any existing value
                           for the specified attribute. See Extended Attributes
                           below for additional details on this option.

Formatting options:
  --tag-format TEMPLATE    Template for specifying Finder tag format. '{GROUP}'
                           will be replaced with group name of tag (as
                           specified by exiftool), '{TAG}' will be replaced by
                           tag name, and '{VALUE}' will be replaced by the tag
                           value. Default tag template is '{GROUP}:{TAG}:
                           {VALUE}' if tag group specified otherwise '{TAG}:
                           {VALUE}'. See Template System for additional
                           details.
  --fc-format TEMPLATE     Template for specifying Finder comment format.
                           '{GROUP}' will be replaced with group name of tag
                           (as specified by exiftool), '{TAG}' will be replaced
                           by tag name, and '{VALUE}' will be replaced by the
                           tag value. Default Finder comment template is
                           '{GROUP}:{TAG}: {VALUE}' if tag group specified
                           otherwise '{TAG}: {VALUE}'. See Template System for
                           additional details.

Options for use with --all-tags, --tag-group, --tag-match: [mutually exclusive]
  -G, --group              Include tag group in Finder tag (for example,
                           'EXIF:Make' instead of 'Make') when used with --all-
                           tags, --tag-group, --tag-match.
  --value                  Use only tag value (not tag name) as Finder tag when
                           used with --all-tags, --tag-group, --tag-match.

Settings:
  -V, --verbose            Show verbose output.
  --walk                   Recursively walk directories.
  --exiftool-path PATH     Optional path to exiftool executable (will look in
                           $PATH if not specified).
  --dry-run                Dry run mode; do not actually modify any Finder
                           metadata.
  --overwrite-tags         Overwrite existing Finder tags (default is to append
                           to existing).
  --overwrite-fc           Overwrite existing Finder comments (default is to
                           append to existing).

Other options:
  --version                Show the version and exit.
  --help                   Show this message and exit.

Tag names used with --tag and --tag-value may be any tag that exiftool can
read. For a complete list of tag values, see https://exiftool.org/TagNames/.
Tag names may be specified with or without the tag group name.  For example:
`--tag Keywords` and `--tag IPTC:Keywords` are both valid. If specified, the
group name will be output to the name of the Finder tag when used with --tag.
For example, `--tag IPTC:Keywords` will result in a Finder tag named
`IPTC:Keywords: Travel` if `Travel` was one of the keywords and `--tag
Keywords` would result in a Finder tag of `Keywords: Travel`. To use only the
tag value as the keyword, use `--tag-value Keywords`, which would result in a
Finder tag named `Travel`.

When used with --tag, Finder tags will be created in format `TagName:
TagValue`. For example, `--tag ISO` would produce something like `ISO: 100`.

exiftool must be installed as it is used to read the metadata from media files.
See https://exiftool.org/ to download and install exiftool.


** Extended Attributes **

The '-xattr-template' option writes additional metadata to extended attributes
in the file.  These option will only work if the destination filesystem
supports extended attributes (most do).  Unlike EXIF metadata, extended
attributes do not modify the actual file.

Note: Most cloud storage services do not synch extended attributes. Dropbox
does sync  them and any changes to a file's extended attributes will cause
Dropbox to re-sync the files.

The following attributes may be used with '--xattr-template':


authors        The author, or authors, of the contents of the file.  A list of
               strings. (com.apple.metadata:kMDItemAuthors)
comment        A comment related to the file.  This differs from the Finder
               comment, kMDItemFinderComment.  A string.
               (com.apple.metadata:kMDItemComment)
copyright      The copyright owner of the file contents.  A string.
               (com.apple.metadata:kMDItemCopyright)
creator        Application used to create the document content (for example
               “Word”, “Pages”, and so on).  A string.
               (com.apple.metadata:kMDItemCreator)
description    A description of the content of the resource.  The description
               may include an abstract, table of contents, reference to a
               graphical representation of content or a free-text account of
               the content.  A string. (com.apple.metadata:kMDItemDescription)
findercomment  Finder comments for this file.  A string.
               (com.apple.metadata:kMDItemFinderComment)
headline       A publishable entry providing a synopsis of the contents of the
               file.  A string. (com.apple.metadata:kMDItemHeadline)
keywords       Keywords associated with this file. For example, “Birthday”,
               “Important”, etc. This differs from Finder tags
               (_kMDItemUserTags) which are keywords/tags shown in the Finder
               and searchable in Spotlight using "tag:tag_name".  A list of
               strings. (com.apple.metadata:kMDItemKeywords)
participants   The list of people who are visible in an image or movie or
               written about in a document. A list of strings.
               (com.apple.metadata:kMDItemParticipants)
projects       The list of projects that this file is part of. For example, if
               you were working on a movie all of the files could be marked as
               belonging to the project “My Movie”. A list of strings.
               (com.apple.metadata:kMDItemProjects)
rating         User rating of this item. For example, the stars rating of an
               iTunes track. An integer. (com.apple.metadata:kMDItemStarRating)
subject        Subject of the this item. A string.
               (com.apple.metadata:kMDItemSubject)
title          The title of the file. For example, this could be the title of a
               document, the name of a song, or the subject of an email
               message. A string. (com.apple.metadata:kMDItemTitle)
version        The version number of this file. A string.
               (com.apple.metadata:kMDItemVersion)

For additional information on extended attributes see: https://developer.apple.
com/documentation/coreservices/file_metadata/mditem/common_metadata_attribute_k
eys


** Template System **

exif2findertags contains a rich templating system which allows fine-grained    
control over the output format of metadata. The templating system converts one 
or template statements, written in exif2findertags templating language, to one 
or more rendered values using metadata information from the photo being        
processed.                                                                     

In its simplest form, a template statement has the form: "{template_field}",   
for example "{Make}" which would resolve to the camera make (EXIF:Make) of the 
photo, for example "Apple" for a photo taken on an iPhone   .                  

Template statements may contain one or more modifiers.  The full syntax is:    

"pretext{delim+template_field:subfield|filter[find,replace]                    
conditional?bool_value,default}posttext"                                       

Template statements are white-space sensitive meaning that white space (spaces,
tabs) changes the meaning of the template statement.                           

pretext and posttext are free form text.  For example, if a photo has Title    
(e.g. XMP:Title) "My Photo Title". the template statement "The title of the    
photo is {Title}", resolves to "The title of the photo is My Photo Title".  The
pretext in this example is "The title if the photo is " and the template_field 
is {Title}.  Note: some punctuation such as commas cannot be used in the       
pretext or posttext.  For this reason, the template system provides special    
punctuation templates like {comma} to insert punctuation where needed. For     
example: {Make}{comma}{Model} could resolve to Apple,iPhone SE.                

delim: optional delimiter string to use when expanding multi-valued template   
values in-place                                                                

+: If present before template name, expands the template in place.  If delim   
not provided, values are joined with no delimiter.                             

e.g. if Photo keywords are ["foo","bar"]:                                      

 • "{keywords}" renders to "foo", "bar"                                        
 • "{,+keywords}" renders to: "foo,bar"                                        
 • "{; +keywords}" renders to: "foo; bar"                                      
 • "{+keywords}" renders to "foobar"                                           

template_field: The template field to resolve.                                 

:subfield: Templates may have sub-fields; reserved for future use.             

|filter: You may optionally append one or more filter commands to the end of   
the template field using the vertical pipe ('|') symbol.  Filters may be       
combined, separated by '|' as in: {keyword|capitalize|parens}.                 

Valid filters are:                                                             

 • lower: Convert value to lower case, e.g. 'Value' => 'value'.                
 • upper: Convert value to upper case, e.g. 'Value' => 'VALUE'.                
 • strip: Strip whitespace from beginning/end of value, e.g. ' Value ' =>      
   'Value'.                                                                    
 • titlecase: Convert value to title case, e.g. 'my value' => 'My Value'.      
 • capitalize: Capitalize first word of value and convert other words to lower 
   case, e.g. 'MY VALUE' => 'My value'.                                        
 • braces: Enclose value in curly braces, e.g. 'value => '{value}'.            
 • parens: Enclose value in parentheses, e.g. 'value' => '(value')             
 • brackets: Enclose value in brackets, e.g. 'value' => '[value]'              
 • shell_quote: Quotes the value for safe usage in the shell, e.g. My file.jpeg
   => 'My file.jpeg'; only adds quotes if needed.                              

e.g. if Photo keywords are ["FOO","bar"]:                                      

 • "{keywords|lower}" renders to "foo", "bar"                                  
 • "{keywords|upper}" renders to: "FOO", "BAR"                                 
 • "{keywords|capitalize}" renders to: "Foo", "Bar"                            
 • "{keywords|lower|parens}" renders to: "(foo)", "(bar)"                      

e.g. if Photo description is "my description":                                 

 • "{Description|titlecase}" renders to: "My Description"                      

[find,replace]: optional text replacement to perform on rendered template      
value.  For example, to replace "/" in a a keyword, you could use the template 
"{keywords[/,-]}".  Multiple replacements can be made by appending "|" and     
adding another find|replace pair.  e.g. to replace both "/" and ":" in         
keywords: "{keywords[/,-|:,-]}".  find/replace pairs are not limited to single 
characters.  The "|" character cannot be used in a find/replace pair.          

conditional: optional conditional expression that is evaluated as boolean      
(True/False) for use with the ?bool_value modifier.  Conditional expressions   
take the form ' not operator value' where not is an optional modifier that     
negates the operator.  Note: the space before the conditional expression is    
required if you use a conditional expression.  Valid comparison operators are: 

 • contains: template field contains value, similar to python's in             
 • matches: template field contains exactly value, unlike contains: does not   
   match partial matches                                                       
 • startswith: template field starts with value                                
 • endswith: template field ends with value                                    
 • <=: template field is less than or equal to value                           
 • >=: template field is greater than or equal to value                        
 • <: template field is less than value                                        
 • >: template field is greater than value                                     
 • ==: template field equals value                                             
 • !=: template field does not equal value                                     

The value part of the conditional expression is treated as a bare (unquoted)   
word/phrase.  Multiple values may be separated by '|' (the pipe symbol).  value
is itself a template statement so you can use one or more template fields in   
value which will be resolved before the comparison occurs.                     

For example:                                                                   

 • {keywords matches Beach} resolves to True if 'Beach' is a keyword. It would 
   not match keyword 'BeachDay'.                                               
 • {keywords contains Beach} resolves to True if any keyword contains the word 
   'Beach' so it would match both 'Beach' and 'BeachDay'.                      
 • {ISO < 100} resolves to True if the photo's ISO is < 100.                   
 • {keywords|lower contains beach} uses the lower case filter to do            
   case-insensitive matching to match any keyword that contains the word       
   'beach'.                                                                    
 • {keywords|lower not contains beach} uses the not modifier to negate the     
   comparison so this resolves to True if there is no keyword that matches     
   'beach'.                                                                    

?bool_value: Template fields may be evaluated as boolean (True/False) by       
appending "?" after the field name or "[find/replace]".  If a field is True or 
has any value, the value following the "?" will be used to render the template 
instead of the actual field value.  If the template field evaluates to False or
has no value (e.g. photo has no title and field is "{Title}") then the default 
value following a "," will be used.                                            

e.g. if photo has a title                                                      

 • "{Title?I have a title,I do not have a title}" renders to "I have a title"  

and if it does not have a title:                                               

 • "{Title?I have a title,I do not have a title}" renders to "I do not have a  
   title"                                                                      

,default: optional default value to use if the template name has no value.     
This modifier is also used for the value if False for boolean-type fields (see 
above) as well as to hold a sub-template for values like {created.strftime}.   
If no default value provided and the field is null, exif2findertags will skip  
that particular template.                                                      

e.g., if photo has no title set,                                               

 • --tag-template "{Title}" would result in no Finder tag being set for this   
   particular photo.                                                           
 • "{title,I have no title}" renders to "I have no title"                      

Template fields such as created.strftime use the default value to pass the     
template to use for strftime.                                                  

e.g., if photo date is 4 February 2020, 19:07:38,                              

 • "{created.strftime,%Y-%m-%d-%H%M%S}" renders to "2020-02-04-190738"         

If you want to include "{" or "}" in the output, use "{openbrace}" or          
"{closebrace}" template substitution.                                          

e.g. "{created.year}/{openbrace}{Title}{closebrace}" would result in           
"2020/{Photo Title}".                                                          

Some templates have additional modifiers that can be appended to the template  
name. For example, the {filepath} template represents the path of the file     
being processed. You can access various parts of the path using the following  
modifiers:                                                                     

 • {filepath.parent}: the parent directory                                     
 • {filepath.name}: the name of the file or final sub-directory                
 • {filepath.stem}: the name of the file without the extension                 
 • {filepath.suffix}: the suffix of the file including the leading '.'         

For example, ff the field {filepath} is '/Shared/Photos/IMG_1234.JPG':         

 • {filepath.parent} is '/Shared/Photos'                                       
 • {filepath.name} is 'IMG_1234.JPG'                                           
 • {filepath.stem} is 'IMG_1234'                                               
 • {filepath.suffix} is '.JPG'                                                 

** Template Substitutions **

Substitution         Description
{Group:Tag}          Any valid exiftool tag with optional group name, e.g.
                     '{EXIF:Make}', '{Make}', '{IPTC:Keywords}', '{ISO}';
                     invalid or missing tags will be ignored.
{GROUP}              The tag group (as defined by exiftool) for the tag being
                     processed, for example, 'EXIF'; for use with --tag-format.
{TAG}                The name of the tag being processed, for example,
                     'ImageDescription'; for use with --tag-format.
{VALUE}              The value of the tag being processed, for example, 'My
                     Image Description'; for use with --tag-format.
{strip}              Use in form '{strip,TEMPLATE}'; strips whitespace from
                     begining and end of rendered TEMPLATE value(s).
{detected_text}      List of text strings found in the image after performing
                     text detection. You may pass a confidence threshold value
                     between 0.0 and 1.0 after a colon as in
                     '{detected_text:0.5}'; The default confidence threshold is
                     0.7. '{detected_text}' works only on macOS Catalina
                     (10.15) or later.
{filepath}           The full path to the file being processed.
{created}            Photo's creation date if set in the EXIF data, otherwise
                     null; ISO 8601 format
{created.date}       Photo's creation date in ISO format, e.g. '2020-03-22'
{created.year}       4-digit year of photo creation time
{created.yy}         2-digit year of photo creation time
{created.mm}         2-digit month of the photo creation time (zero padded)
{created.month}      Month name in user's locale of the photo creation time
{created.mon}        Month abbreviation in the user's locale of the photo
                     creation time
{created.dd}         2-digit day of the month (zero padded) of photo creation
                     time
{created.dow}        Day of week in user's locale of the photo creation time
{created.doy}        3-digit day of year (e.g Julian day) of photo creation
                     time, starting from 1 (zero padded)
{created.hour}       2-digit hour of the photo creation time
{created.min}        2-digit minute of the photo creation time
{created.sec}        2-digit second of the photo creation time
{created.strftime}   Apply strftime template to file creation date/time. Should
                     be used in form {created.strftime,TEMPLATE} where TEMPLATE
                     is a valid strftime template, e.g.
                     {created.strftime,%Y-%U} would result in year-week number
                     of year: '2020-23'. If used with no template will return
                     null value. See https://strftime.org/ for help on strftime
                     templates.
{modified}           Photo's modification date if set in the EXIF data,
                     otherwise null; ISO 8601 format
{modified.date}      Photo's modification date in ISO format, e.g.
                     '2020-03-22'; uses creation date if photo is not modified
{modified.year}      4-digit year of photo modification time; uses creation
                     date if photo is not modified
{modified.yy}        2-digit year of photo modification time; uses creation
                     date if photo is not modified
{modified.mm}        2-digit month of the photo modification time (zero
                     padded); uses creation date if photo is not modified
{modified.month}     Month name in user's locale of the photo modification
                     time; uses creation date if photo is not modified
{modified.mon}       Month abbreviation in the user's locale of the photo
                     modification time; uses creation date if photo is not
                     modified
{modified.dd}        2-digit day of the month (zero padded) of the photo
                     modification time; uses creation date if photo is not
                     modified
{modified.dow}       Day of week in user's locale of the photo modification
                     time; uses creation date if photo is not modified
{modified.doy}       3-digit day of year (e.g Julian day) of photo modification
                     time, starting from 1 (zero padded); uses creation date if
                     photo is not modified
{modified.hour}      2-digit hour of the photo modification time; uses creation
                     date if photo is not modified
{modified.min}       2-digit minute of the photo modification time; uses
                     creation date if photo is not modified
{modified.sec}       2-digit second of the photo modification time; uses
                     creation date if photo is not modified
{modified.strftime}  Apply strftime template to file modification date/time.
                     Should be used in form {modified.strftime,TEMPLATE} where
                     TEMPLATE is a valid strftime template, e.g.
                     {modified.strftime,%Y-%U} would result in year-week number
                     of year: '2020-23'. If used with no template will return
                     null value. Uses creation date if photo is not modified.
                     See https://strftime.org/ for help on strftime templates.
{today.date}         Current date in iso format, e.g. '2020-03-22'
{today.year}         4-digit year of current date
{today.yy}           2-digit year of current date
{today.mm}           2-digit month of the current date (zero padded)
{today.month}        Month name in user's locale of the current date
{today.mon}          Month abbreviation in the user's locale of the current
                     date
{today.dd}           2-digit day of the month (zero padded) of current date
{today.dow}          Day of week in user's locale of the current date
{today.doy}          3-digit day of year (e.g Julian day) of current date,
                     starting from 1 (zero padded)
{today.hour}         2-digit hour of the current date
{today.min}          2-digit minute of the current date
{today.sec}          2-digit second of the current date
{today.strftime}     Apply strftime template to current date/time. Should be
                     used in form {today.strftime,TEMPLATE} where TEMPLATE is a
                     valid strftime template, e.g. {today.strftime,%Y-%U} would
                     result in year-week number of year: '2020-23'. If used
                     with no template will return null value. See
                     https://strftime.org/ for help on strftime templates.
{comma}              A comma: ','
{semicolon}          A semicolon: ';'
{questionmark}       A question mark: '?'
{pipe}               A vertical pipe: '|'
{openbrace}          An open brace: '{'
{closebrace}         A close brace: '}'
{openparens}         An open parentheses: '('
{closeparens}        A close parentheses: ')'
{openbracket}        An open bracket: '['
{closebracket}       A close bracket: ']'
{newline}            A newline: '\n'
{lf}                 A line feed: '\n', alias for {newline}
{cr}                 A carriage return: '\r'
{crlf}               a carriage return + line feed: '\r\n'
```

Tag names must be valid names as specified in the exiftool [documentation](https://exiftool.org/TagNames/).  The group name may be omitted or included in same format as exfitool uses when run with `exiftool -G -j file.jpg`.

For example:

- `--tag Keywords` or `-tag IPTC:Keywords`
- `--tag-value PersonInImage` or `--tag-value XMP:PersonInImage`

`--tag TAGNAME` will produce a Finder tag named: "TAGNAME: Value" in the same format as the tag name was specified (e.g. with or without group name).  For exmaple:

- `Keywords: Travel` or `IPTC:Keywords: Travel`

`--tag-value` will produce a Finder tag named with just the value of the specified tag without the tag name.  For example:

- `Jane Smith` instead of `PersonInImage: Jane Smith`

# Contributing

Feedback and contributions of all kinds welcome!  Please open an [issue](https://github.com/RhetTbull/exif2findertags/issues) if you would like to suggest enhancements or bug fixes.

# Related Projects

- [osxphotos](https://github.com/RhetTbull/osxphotos) export photos and metadata from Apple Photos.  Includes ability to write data to Finder tags and comments like exif2findertags.
