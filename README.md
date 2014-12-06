``` UNDER CONSTRUCTION - DO NOT USE```

## Specs

https://github.com/typesafehub/config/blob/master/HOCON.md

## Usage

    from pyhocon import ConfigFactory
    
    conf = ConfigFactory.load('tests/config1.conf')
    conf.get_string('application.hostname')
    
## TODO

TODO list taken from: https://github.com/primexx/hocon-config

**Completed Items** marked as `COMPLETE`

Items                                  | Status
-------------------------------------- | :-----:
Comments                               | `x`
Omit root braces                       | `COMPLETE`
Key-value separator                    | `COMPLETE`
Duplicate keys and object merging      | `x`
Unquoted strings                       | `COMPLETE`
Multi-line strings                     | `COMPLETE`
String value concatenation             | `x`
Array and object concatenation         | `x`
Arrays without commas                  | `x`
Path expressions                       | `x`
Paths as keys                          | `x`
Substitutions                          | `x`
Self-referential substitutions         | `x`
The `+=` separator                     | `x`
Includes                               | `x`
Include semantics: merging                         | `x`
Include semantics: substitution                    | `x`
Include semantics: missing files                   | `x`
Include semantics: file formats and extensions     | `x`
Include semantics: locating resources              | `x`

API Recommendations                                        | Status
---------------------------------------------------------- | :----:
Conversion of numerically-index objects to arrays          | `x`
Conversion of numerically-index objects to arrays          | `x`


