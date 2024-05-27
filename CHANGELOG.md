# Changelog

# Version 0.3.60

* Update pyparsing requirement from ~=2.0 to >=2,<4 (@ecederstrand) [#296]
* Fixes for dict substitution (@USSX-Hares) [#292]
* Fix: Tests on Windows (@USSX-Hares) [#291]
* Fix broken overrides (@afanasev) [#287]

# Version 0.3.59

* Resolve namespace package (@yifeitao) [#264]
* Update pyparsing requires lock to be more strict [#275]

# Version 0.3.58

* Adding the resolve method to resolve substitution keys in 1 config tree with another config tree (@borissmidt) [#266]
* Support serializing timedelta and relativedelta to string (hocon, json etc.) (@gabis-precog) [#263]
* Upgrade to GitHub-native Dependabot (@dependabot-preview) [#260]
* Process substitution overrides in order (@JettJones) [#257]
* Fix duration parsing in lists (@olii) [#255]
* Add support for Python 3.9 and fix deprecation warning (@olii) [#254]

# Version 0.3.57

* Rewrite the logic to resolve package-relative paths so we can remove the "asset" library (@klamann) [#247]

# Version 0.3.56

* fix include error with chinese strings (@xinghaixu) [#240]
* Glob-pattern Includes (@USSX-Hares) [#236]
* Fix parsing of durations/periods (@olii) [#237]
* Fix config_parser.py docstrings (@LysanderGG) [#235]

# Version 0.3.55

* Add test for include substitution (@gpoulin) [#217]
* Fix self references when environment variables exist (@anujkumar93) [#219]
* Remove inactive Gitter channel from README (@scottj97) [#255]
* Fix STR_SUBSTITUTION, because ConfigSubstitution has no function raw_str (@manso92) [#227]
* Add support for package include (@mrijken) [#228]
* Fix required(file()) syntax (@jrouly) [#229]

# Version 0.3.54

* Fix self references when environment variables exist (@anujkumar93) [#219]

# Version 0.3.53

* Fix JSON and HOCON string escaping (@dtarakanov1) [#209]

# Version 0.3.52

* Add samples to MANIFEST.in/sdist (@chreekat) [#203]
* Use std json library to fix json string escaping (@bdmartin) [#202]

# Version 0.3.51

* Added partial implementation of hocon duration and period recommended api (@gabis-precog) [#199]

# Version 0.3.50

* Do not unquote keys containing special characters (@Tommassino) [#198]

# Version 0.3.49

* Return None instead of NoneValue when using items() method (@roee-allegro) [#196]
* Add context for changing default chars to avoid conflict with other dependencies using pyparsing (@chunyang-wen) [#195]

# Version 0.3.48

* Support conversion of numerically-index objects to arrays (a.1 = 4) (@lune-sta) [#189]
* Handle ConfigValues and ConfigSubstitution in HOCONConverter.to_hocon (@ChristopheDuong) [#192]
* Fix raising of ConfigException for get_int() and get_float() (@ElkMonster) [#188]
* Fixed Flake8 error for Python 2.7

# Version 0.3.47

* Fixed negative integer parsing [#185]

# Version 0.3.46

* Fixed forbidden characters (@sambible) [#184]

# Version 0.3.45

* Fixed scientific notation parsing (@chunyang-wen) [#177]

# Version 0.3.44

* Escape backslash (@roee-allegro) [#173]
* Fixed incorrect config merge (@aalba6675) [#170]

# Version 0.3.43
* Support slash character / in keys (@richard534) [#166]

# Version 0.3.42
* Added resolve option to with_fallback (@afanasev) [#164]
* Allow unresolved substitution to use default string or substitution string (e.g., ${abc}) [#163]
* Fixed tool (@derkcrezee). [#161]

# Version 0.3.41
* Fixed escaped quotes inside quoted and unquoted string (@darthbear) [#158]

# Version 0.3.40
* Fix non-root ConfigTree merge onto root ConfigTree (@aalba6675) [#156]
* Unresolved optional substitutions work with config merging (@aalba6675) [#153]

# Version 0.3.39
* Fixed self ref substitution (@aalba6675) [#142]
* Fixed with_fallback to not mutate config (@aalba6675) [#143]
* Fixed self reference (@aalba6675) [#146]
* Fixed complex substitutions (@aalba6675) [#148]
* Support attribute path a.b.c. (@chunyang-wen) [#150]
* Updated python version (@hugovk) [#151]


# Version 0.3.38
* Added compact option for hocon output. #129
* Unicode fix for unquoted strings. #130

# Version 0.3.37

* Dropped support for Python 2.6 (wheel)
* Fixed get_xxx() methods to return None if the value is None. PR [#128]
* Added required includes. PR[#127]
* Config tree fix for pop. PR[#126]
* Handle None value for converting methods. PR[#124]
* ConfigTree.pop() should delete key when value == default_value. PR[#123]

# Version 0.3.36

* Fixed tripled quoted string parsing bug. PR [#119]
* Added pop() method to ConfigTree and added KeyError to ConfigMissingException. PR [#120]

# Version 0.3.35

* Implemented contains method. PR [#108]
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

* Fixed dictionary substitution merge. PR[#52]

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

* Fixed substitutions that are overridden later on by a non substitution. PR[#34]
* Added logging. PR[#30] and PR[#31]

# Version 0.3.3

* Fixed optional substitution when overriding elements at the same level. PR[#28]
* Silent IOErrors when including nonexistent files. PR[#24]
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
