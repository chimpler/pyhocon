pyhocon
=======

[![Build Status](https://travis-ci.org/chimpler/pyhocon.svg)](https://travis-ci.org/chimpler/pyhocon)

HOCON parser for Python (under construction)

## Specs

https://github.com/typesafehub/config/blob/master/HOCON.md

## Usage

    from pyhocon import ConfigFactory
    
    conf = ConfigFactory.parse_file('samples/database.conf')
    host = conf.get_string('databases.mysql.host')
    port = conf['databases.mysql.port']
    username = conf['databases']['mysql']['username']
    password = conf.get_config('databases')['mysql.password']
  
## TODO

TODO list taken from: https://github.com/primexx/hocon-config

**Completed Items** marked as `COMPLETE`

Items                                  | Status
-------------------------------------- | :-----:
Comments                               | `COMPLETE`
Omit root braces                       | `COMPLETE`
Key-value separator                    | `COMPLETE`
Duplicate keys and object merging      | `COMPLETE`
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
