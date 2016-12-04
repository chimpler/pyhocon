# Changelog

# Version 0.3.35

* Implemented contains method . PR [#108]
* Fixed bug where last line is a comment. PR [#109]

# Version 0.3.34

* Fixed some error handling that was unable to deal with unicode keys. PR [#99]
* Fixed Python 2.6 incompatible format string. PR [#100]

# Version 0.3.33

* Fix unicode dict key. PR [#94]

# Version 0.3.32

* Bug fix for include file. PR [#93]

# Version 0.3.31

* Bug fix for variables that start with include-blabla. PR [#92]

# Version 0.3.30

* Bug fix for ConfigTree.get_bool(). PR [#90]

# Version 0.3.29

* Don't lock pyparsing to a specific version. PR [#86]

# Version 0.3.28 

* Quoted str ws fix. PR [#85]

# Version 0.3.27 

* Fixes for self-reference resolution after merging configs. PR [#82]
* Key with dots. PR [#83]

# Version 0.3.26 

* Implemented self-referential substitutions and +=. PR [#81]

# Version 0.3.25

* ConfigValue.transform: do not wrap lists. PR [#76]

# Version 0.3.24

* Use recursive merging when concatenating objects. PR [#74]

# Version 0.3.23

* Handle unreachable URL include. PR [#73]

# Version 0.3.22

* Bumped pycparsing to 2.1.1. PR [#72]

# Version 0.3.21

* Fixed from_dict. PR [#71]

# Version 0.3.20

* Updated pycparsing to 2.1.0. PR [#70]

# Version 0.3.19

* Fixed unresolved optional substitution logic. PR[#69]

# Version 0.3.18

* Bumped pyparsing from 2.0.3 to 2.0.6. PR[#68]

# Version 0.3.17

* Bugfix for nested substitution failure. PR[#64]

# Version 0.3.16

* Support \r and no eol on last line. PR[#61]

# Version 0.3.15

* Added ConfigTree.merge_configs(). PR[#57]
* Fixed substitution with spaces PR[#59]

# Version 0.3.14

* Added argparse as a dependency if being installed on Python 2.6. PR[#54]

# Version 0.3.13

* Fixed dictionary substititution merge. PR[#52]

# Version 0.3.12

* Fixed list merge. PR[#51]

# Version 0.3.11

* Added default indent to 2. PR[#47]
* Fix dotted notation merge. PR[#49]

# Version 0.3.10

* Backward compatibility with imports

# Version 0.3.9

* Added from_dict to convert a dict or ordered dict into a config tree. PR[#42]

# Version 0.3.8

* Fix multi line string (don't escape). PR[#41]
* Added HOCON export. PR[#40]

# Version 0.3.7

* Added with_fallback method. PR[#38]

# Version 0.3.6

* Added with_fallback method. PR[#37]

# Version 0.3.5

* Fixed substitutions to be evaluated after all files are loaded. PR[#36]

# Version 0.3.4

* Fixed substitutions that are overriden later on by a non substitution. PR[#34]
* Added logging. PR[#30] and PR[#31]

# Version 0.3.3

* Fixed optional substitution when overriding elements at the same level. PR[#28]
* Silent IOErrors when including non-existent files. PR[#24]
* Fixed when assign key to a value, list or dict that starts with eol. PR[#22]

## Version 0.3.2

* implemented optional substitution (e.g., ${?abc}) and fixed substitution logic when having dict merge. PR[#20]

## Version 0.3.1

* can specify default value in get, get_int, ... PR[#17]

## Version 0.3.0

* fixed list of dict merge and includes in list. PR [#16]

## Version 0.2.9

* fixed expression assignment (only dictionaries with no concat can omit the : or = sign). PR [#15]

## Version 0.2.8

* fixed parse_URL

## Version 0.2.7

* fixed dict merge. PR [#14]

## Version 0.2.6

* fixed string substitutions. PR [#13]

## Version 0.2.5

* added list and dict inheritance. PR [#11]

## Version 0.2.4

* added python 2.6 support. PR [#8]

## Version 0.2.3

* fixed bug when we insert None values that shouldn't raise an exception when getting them. PR [#7]

## Version 0.2.2

* simplified code (ConfigTree extends OrderedDict) and other features. PR [#6]
