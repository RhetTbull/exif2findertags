exif2findertags contains a rich templating system which allows fine-grained control over the output format of metadata. The templating system converts one or template statements, written in exif2findertags metadata templating language, to one or more rendered values using metadata information from the photo being processed. 

In its simplest form, a template statement has the form: `"{template_field}"`, for example `"{Make}"` which would resolve to the camera make (`EXIF:Make`) of the photo, for example `"Apple"` for a photo taken on an iPhone   .

Template statements may contain one or more modifiers.  The full syntax is:

`"pretext{delim+template_field:subfield|filter[find,replace] conditional?bool_value,default}posttext"`

Template statements are white-space sensitive meaning that white space (spaces, tabs) changes the meaning of the template statement.

`pretext` and `posttext` are free form text.  For example, if a photo has Title (e.g. XMP:Title) "My Photo Title". the template statement `"The title of the photo is {Title}"`, resolves to `"The title of the photo is My Photo Title"`.  The `pretext` in this example is `"The title if the photo is "` and the template_field is `{Title}`.  Note: some punctuation such as commas cannot be used in the pretext or posttext.  For this reason, the template system provides special punctuation templates like `{comma}` to insert punctuation where needed. For example: `{Make}{comma}{Model}` could resolve to `Apple,iPhone SE`. 


`delim`: optional delimiter string to use when expanding multi-valued template values in-place

`+`: If present before template `name`, expands the template in place.  If `delim` not provided, values are joined with no delimiter.

e.g. if Photo keywords are `["foo","bar"]`:

- `"{keywords}"` renders to `"foo", "bar"`
- `"{,+keywords}"` renders to: `"foo,bar"`
- `"{; +keywords}"` renders to: `"foo; bar"`
- `"{+keywords}"` renders to `"foobar"`

`template_field`: The template field to resolve.  

`:subfield`: Templates may have sub-fields; reserved for future use.

`|filter`: You may optionally append one or more filter commands to the end of the template field using the vertical pipe ('|') symbol.  Filters may be combined, separated by '|' as in: `{keyword|capitalize|parens}`.

Valid filters are:

- lower: Convert value to lower case, e.g. 'Value' => 'value'.
- upper: Convert value to upper case, e.g. 'Value' => 'VALUE'.
- strip: Strip whitespace from beginning/end of value, e.g. ' Value ' => 'Value'.
- titlecase: Convert value to title case, e.g. 'my value' => 'My Value'.
- capitalize: Capitalize first word of value and convert other words to lower case, e.g. 'MY VALUE' => 'My value'.
- braces: Enclose value in curly braces, e.g. 'value => '{value}'.
- parens: Enclose value in parentheses, e.g. 'value' => '(value')
- brackets: Enclose value in brackets, e.g. 'value' => '[value]'
- shell_quote: Quotes the value for safe usage in the shell, e.g. My file.jpeg => 'My file.jpeg'; only adds quotes if needed.
<!-- 
- function: Run custom python function to filter value; use in format 'function:/path/to/file.py::function_name'. See example at https://github.com/RhetTbull/osxphotos/blob/master/examples/template_filter.py
-->

e.g. if Photo keywords are `["FOO","bar"]`:

- `"{keywords|lower}"` renders to `"foo", "bar"`
- `"{keywords|upper}"` renders to: `"FOO", "BAR"`
- `"{keywords|capitalize}"` renders to: `"Foo", "Bar"`
- `"{keywords|lower|parens}"` renders to: `"(foo)", "(bar)"`

e.g. if Photo description is "my description":

- `"{Description|titlecase}"` renders to: `"My Description"`

`[find,replace]`: optional text replacement to perform on rendered template value.  For example, to replace "/" in a a keyword, you could use the template `"{keywords[/,-]}"`.  Multiple replacements can be made by appending "|" and adding another find|replace pair.  e.g. to replace both "/" and ":" in keywords: `"{keywords[/,-|:,-]}"`.  find/replace pairs are not limited to single characters.  The "|" character cannot be used in a find/replace pair.

`conditional`: optional conditional expression that is evaluated as boolean (True/False) for use with the `?bool_value` modifier.  Conditional expressions take the form '` not operator value`' where `not` is an optional modifier that negates the `operator`.  Note: the space before the conditional expression is required if you use a conditional expression.  Valid comparison operators are:

- `contains`: template field contains value, similar to python's `in`
- `matches`: template field contains exactly value, unlike `contains`: does not match partial matches
- `startswith`: template field starts with value
- `endswith`: template field ends with value
- `<=`: template field is less than or equal to value
- `>=`: template field is greater than or equal to value
- `<`: template field is less than value
- `>`: template field is greater than value
- `==`: template field equals value
- `!=`: template field does not equal value

The `value` part of the conditional expression is treated as a bare (unquoted) word/phrase.  Multiple values may be separated by '|' (the pipe symbol).  `value` is itself a template statement so you can use one or more template fields in `value` which will be resolved before the comparison occurs.

For example:

- `{keywords matches Beach}` resolves to True if 'Beach' is a keyword. It would not match keyword 'BeachDay'.
- `{keywords contains Beach}` resolves to True if any keyword contains the word 'Beach' so it would match both 'Beach' and 'BeachDay'.
- `{ISO < 100}` resolves to True if the photo's ISO is < 100.
- `{keywords|lower contains beach}` uses the lower case filter to do case-insensitive matching to match any keyword that contains the word 'beach'.
- `{keywords|lower not contains beach}` uses the `not` modifier to negate the comparison so this resolves to True if there is no keyword that matches 'beach'.

`?bool_value`: Template fields may be evaluated as boolean (True/False) by appending "?" after the field name or "[find/replace]".  If a field is True or has any value, the value following the "?" will be used to render the template instead of the actual field value.  If the template field evaluates to False or has no value (e.g. photo has no title and field is `"{Title}"`) then the default value following a "," will be used.  

e.g. if photo has a title

- `"{Title?I have a title,I do not have a title}"` renders to `"I have a title"`

and if it does not have a title: 

- `"{Title?I have a title,I do not have a title}"` renders to `"I do not have a title"`

`,default`: optional default value to use if the template name has no value.  This modifier is also used for the value if False for boolean-type fields (see above) as well as to hold a sub-template for values like `{created.strftime}`.  If no default value provided and the field is null, exif2findertags will skip that particular template.   

e.g., if photo has no title set,

- `--tag-template "{Title}"` would result in no Finder tag being set for this particular photo. 
- `"{title,I have no title}"` renders to `"I have no title"`

Template fields such as `created.strftime` use the default value to pass the template to use for `strftime`.  

e.g., if photo date is 4 February 2020, 19:07:38,

- `"{created.strftime,%Y-%m-%d-%H%M%S}"` renders to `"2020-02-04-190738"`

If you want to include "{" or "}" in the output, use "{openbrace}" or "{closebrace}" template substitution.

e.g. `"{created.year}/{openbrace}{Title}{closebrace}"` would result in `"2020/{Photo Title}"`.

Some templates have additional modifiers that can be appended to the template name. For example, the {filepath} template represents the path of the file being processed. You can access various parts of the path using the following modifiers:

- `{filepath.parent}`: the parent directory
- `{filepath.name}`: the name of the file or final sub-directory
- `{filepath.stem}`: the name of the file without the extension
- `{filepath.suffix}`: the suffix of the file including the leading '.'

For example, ff the field `{filepath}` is `'/Shared/Photos/IMG_1234.JPG'`:

- `{filepath.parent}` is `'/Shared/Photos'`
- `{filepath.name}` is `'IMG_1234.JPG'`
- `{filepath.stem}` is `'IMG_1234'`
- `{filepath.suffix}` is `'.JPG'`
