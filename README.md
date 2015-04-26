pyhocon
=======

[![Join the chat at https://gitter.im/chimpler/pyhocon](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/chimpler/pyhocon?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![pypi](http://img.shields.io/pypi/v/pyhocon.png)](https://pypi.python.org/pypi/pyhocon)
[![Supported Python Versions](https://pypip.in/py_versions/pyhocon/badge.svg)](https://pypi.python.org/pypi/pyhocon/)
[![pypi downloads](http://img.shields.io/pypi/dm/pyhocon.png)](https://pypi.python.org/pypi/pyhocon)
[![Build Status](https://travis-ci.org/chimpler/pyhocon.svg)](https://travis-ci.org/chimpler/pyhocon)
[![License](https://pypip.in/license/pyhocon/badge.svg)](https://pypi.python.org/pypi/pyhocon/)
[![Coverage Status](https://coveralls.io/repos/chimpler/pyhocon/badge.svg)](https://coveralls.io/r/chimpler/pyhocon)

HOCON parser for Python

## Specs

https://github.com/typesafehub/config/blob/master/HOCON.md

# Installation

It is available on pypi so you can install it as follows:

    $ pip install pyhocon

## Usage

The parsed config can be seen as a nested dictionary (with types automatically inferred) where values can be accessed using normal
dictionary getter (e.g., `conf['a']['b']` or using paths like `conf['a.b']`) or via the methods `get`, `get_int` (throws an exception
if it is not an int), `get_string`, `get_list`, `get_float`, `get_bool`, `get_config`.

    from pyhocon import ConfigFactory

    conf = ConfigFactory.parse_file('samples/database.conf')
    host = conf.get_string('databases.mysql.host')
    same_host = conf.get('databases.mysql.host')
    same_host = conf['databases.mysql.host']
    same_host = conf['databases']['mysql.host']
    port = conf['databases.mysql.port']
    username = conf['databases']['mysql']['username']
    password = conf.get_config('databases')['mysql.password']
    password = conf.get('databases.mysql.password', 'default_password')

## Example of HOCON file

    //
    // You can use # or // for comments
    //
    {
      databases {
        # MySQL
        active = true
        enable_logging = false
        resolver = null
        # you can use substitution with unquoted strings. If it it not found in the document, it defaults to environment variables
        home_dir = ${HOME} # you can substitute with environment variables
        "mysql" = {
          host = "abc.com" # change it
          port = 3306 # default
          username: scott // can use : or =
          password = tiger, // can optionally use a comma
          // number of retries
          retries = 3
        }
      }

      // multi line support
      motd = """
                Hello "man"!
                How is it going?
             """
      // this will be appended to the databases dictionary above
      databases.ips = [
        192.168.0.1 // use white space or comma as separator
        "192.168.0.2" // optional quotes
        192.168.0.3, # can have a trailing , which is ok
      ]

      # you can use substitution with unquoted strings
      retries_msg = You have ${databases.mysql.retries} retries
    }

    // dict merge
    data-center-generic = { cluster-size = 6 }
    data-center-east = ${data-center-generic} { name = "east" }

    // list merge
    default-jvm-opts = [-XX:+UseParNewGC]
    large-jvm-opts = ${default-jvm-opts} [-Xm16g]

## Conversion tool

We provide a conversion tool to convert from HOCON to the JSON, .properties and YAML formats.

    usage: pyhocon [-h] [-i INPUT] [-o OUTPUT] [-f FORMAT]

    pyhocon tool

    optional arguments:
      -h, --help            show this help message and exit
      -i INPUT, --input INPUT FILE
      -o OUTPUT, --output OUTPUT FILE
      -f FORMAT, --format FORMAT
                            output format: json, properties or yaml

If `-i` is omitted, the tool will read from the standard input. If `-o` is omitted, the result will be written to the standard output.

####  JSON

    $ cat samples/database.conf | pyhocon -f json

    {
      "databases": {
        "active": true,
        "enable_logging": false,
        "resolver": null,
        "home_dir": "/Users/darthbear",
        "mysql": {
          "host": "abc.com",
          "port": 3306,
          "username": "scott",
          "password": "tiger",
          "retries": 3
        },
        "ips": [
          "192.168.0.1",
          "192.168.0.2",
          "192.168.0.3"
        ]
      },
      "motd": "\n            Hello \"man\"!\n            How is it going?\n         ",
      "retries_msg": "You have 3 retries"
    }

####  .properties

    $ cat samples/database.conf | pyhocon -f properties

    databases.active = true
    databases.enable_logging = false
    databases.home_dir = /Users/darthbear
    databases.mysql.host = abc.com
    databases.mysql.port = 3306
    databases.mysql.username = scott
    databases.mysql.password = tiger
    databases.mysql.retries = 3
    databases.ips.0 = 192.168.0.1
    databases.ips.1 = 192.168.0.2
    databases.ips.2 = 192.168.0.3
    motd = \
                Hello "man"\!\
                How is it going?\

    retries_msg = You have 3 retries

#### YAML

    $ cat samples/database.conf | pyhocon -f yaml

    databases:
      active: true
      enable_logging: false
      resolver: None
      home_dir: /Users/darthbear
      mysql:
        host: abc.com
        port: 3306
        username: scott
        password: tiger
        retries: 3
      ips:
        - 192.168.0.1
        - 192.168.0.2
        - 192.168.0.3
    motd: |

                Hello "man"!
                How is it going?

    retries_msg: You have 3 retries

## Includes

We support the include semantics using one of the followings:

    include "test.conf"
    include "http://abc.com/test.conf"
    include "https://abc.com/test.conf"
    include "file://abc.com/test.conf"
    include file("test.conf")
    include url("http://abc.com/test.conf")
    include url("https://abc.com/test.conf")
    include url("file://abc.com/test.conf")

When one uses a relative path (e.g., test.conf), we use the same directory as the file that includes the new file as a base directory. If
the standard input is used, we use the current directory as a base directory.

For example if we have the following files:

cat.conf:

    {
      garfield: {
        say: meow
      }
    }

dog.conf:

    {
      mutt: {
        say: woof
        hates: {
          garfield: {
            notes: I don't like him
            say: meeeeeeeooooowww
          }
          include "cat.conf"
        }
      }
    }

animals.conf:

    {
      cat : {
        include "cat.conf"
      }

      dog: {
        include "dog.conf"
      }
    }

Then evaluating animals.conf will result in the followings:

    $ pyhocon -i samples/animals.conf
    {
      "cat": {
        "garfield": {
          "say": "meow"
        }
      },
      "dog": {
        "mutt": {
          "say": "woof",
          "hates": {
            "garfield": {
              "notes": "I don't like him",
              "say": "meow"
            }
          }
        }
      }
    }

As you can see, the attributes in cat.conf were merged to the ones in dog.conf. Note that the attribute "say" in dog.conf got overwritten by the one in cat.conf.

## TODO

Items                                  | Status
-------------------------------------- | :-----:
Comments                               | :white_check_mark:
Omit root braces                       | :white_check_mark:
Key-value separator                    | :white_check_mark:
Commas                                 | :white_check_mark:
Whitespace                             | :white_check_mark:
Duplicate keys and object merging      | :white_check_mark:
Unquoted strings                       | :white_check_mark:
Multi-line strings                     | :white_check_mark:
String value concatenation             | :white_check_mark:
Array concatenation                    | :white_check_mark:
Object concatenation                   | :white_check_mark:
Arrays without commas                  | :white_check_mark:
Path expressions                       | :x:
Paths as keys                          | :white_check_mark:
Substitutions                          | :white_check_mark:
Self-referential substitutions         | :x:
The `+=` separator                     | :x:
Includes                               | :white_check_mark:
Include semantics: merging             | :white_check_mark:
Include semantics: substitution        | :white_check_mark:
Include semantics: missing files       | :x:
Include semantics: file formats and extensions     | :x:
Include semantics: locating resources              | :x:
Include semantics: preventing cycles               | :x:
Conversion of numerically-index objects to arrays  | :x:

API Recommendations                                        | Status
---------------------------------------------------------- | :----:
Conversion of numerically-index objects to arrays          | :x:
Automatic type conversions                                 | :x:
Units format                                               | :x:
Duration format                                            | :x:
Size in bytes format                                       | :x:
Config object merging and file merging                     | :x:
Java properties mapping                                    | :x:

### Contributors

  - Aleksey Ostapenko ([@kbabka](https://github.com/kbakba))
  - Martynas Mickevičius ([@2m](https://github.com/2m))
  - Joe Halliwell ([@joehalliwell](https://github.com/joehalliwell))
  - Tasuku Okuda ([@okdtsk](https://github.com/okdtsk))
  - Uri Laserson ([@laserson](https://github.com/laserson))

### Thanks

  - Agnibha ([@agnibha](https://github.com/agnibha))
  - Ernest Mishkin ([@eric239](https://github.com/eric239))
