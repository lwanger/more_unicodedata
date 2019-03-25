# more_unicodedata
Python library of utilities for extended Unicode data. Leaves off where unicodedata library ends.

This library is an early draft and a work in progress.

It currently has:
* code to parse and write Python data structures for Unicode data files from unicode.org
* map files (Python data structures) for Unicode v11.0.0 as created by the parsers
* functions to help with intentionally confusing characters (detect them or fix them)
* Get the code blocks for a string
* Show if a string has any characters in reserved blocks
* Get the identifierStatus and identifierType for a character
* Check if a string is a valid Unicode identifier
* Check if a string is safe by the Unicode security recommendations (still partially done.)

TODO:
* Implement the rest of is_safe_string
* Parse and add functions for emoji data
* Make this an installable package
* Lots more...

Len Wanger, 2019
