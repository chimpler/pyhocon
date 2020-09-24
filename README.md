pyhocon
=======

[![pypi](http://img.shields.io/pypi/v/pyhocon.png)](https://pypi.python.org/pypi/pyhocon)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/Pyhocon.svg)](https://pypi.python.org/pypi/pyhocon/)
[![Build Status](https://travis-ci.org/chimpler/pyhocon.svg)](https://travis-ci.org/chimpler/pyhocon)
[![Downloads](https://img.shields.io/pypi/dm/pyhocon.svg)](https://pypistats.org/packages/pyhocon)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/684cdd4d82734702ac612bf8b25fc5a0)](https://www.codacy.com/app/francois-dangngoc/pyhocon?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=chimpler/pyhocon&amp;utm_campaign=Badge_Grade)
[![License](https://img.shields.io/pypi/l/Pyhocon.svg)](https://pypi.python.org/pypi/pyhocon/)
[![Coverage Status](https://coveralls.io/repos/chimpler/pyhocon/badge.svg)](https://coveralls.io/r/chimpler/pyhocon)
[![Requirements Status](https://requires.io/github/chimpler/pyhocon/requirements.svg?branch=master)](https://requires.io/github/chimpler/pyhocon/requirements/?branch=master)

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
```python
from pyhocon import ConfigFactory

conf = ConfigFactory.parse_file('samples/database.conf')
host = conf.get_string('databases.mysql.host')
same_host = conf.get('databases.mysql.host')
same_host = conf['databases.mysql.host']
same_host = conf['databases']['mysql.host']
port = conf['databases.mysql.port']
username = conf['databases']['mysql']['username']
password = conf.get_config('databases')['mysql.password']
password = conf.get('databases.mysql.password', 'default_password') #  use default value if key not found
```

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

      # retries message will be overriden if environment variable CUSTOM_MSG is set
      retries_msg = ${?CUSTOM_MSG}
    }

    // dict merge
    data-center-generic = { cluster-size = 6 }
    data-center-east = ${data-center-generic} { name = "east" }

    // list merge
    default-jvm-opts = [-XX:+UseParNewGC]
    large-jvm-opts = ${default-jvm-opts} [-Xm16g]

## Conversion tool

We provide a conversion tool to convert from HOCON to the JSON, .properties and YAML formats.

```
usage: tool.py [-h] [-i INPUT] [-o OUTPUT] [-f FORMAT] [-n INDENT] [-v]

pyhocon tool

optional arguments:
  -h, --help                 show this help message and exit
  -i INPUT, --input INPUT    input file
  -o OUTPUT, --output OUTPUT output file
  -c, --compact              compact format
  -f FORMAT, --format FORMAT output format: json, properties, yaml or hocon
  -n INDENT, --indent INDENT indentation step (default is 2)
  -v, --verbosity            increase output verbosity
```

If `-i` is omitted, the tool will read from the standard input. If `-o` is omitted, the result will be written to the standard output.
If `-c` is used, HOCON will use a compact representation for nested dictionaries of one element (e.g., `a.b.c = 1`)

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
    include required(file("test.conf"))
    include url("http://abc.com/test.conf")
    include url("https://abc.com/test.conf")
    include url("file://abc.com/test.conf")
    include package("package:assets/test.conf")

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

## Duration/Period support

### Difference from HOCON spec

* **nanoseconds** supported only in the sense that it is converted to **microseconds** with lowered accuracy (divided by 1000 and rounded to int).
* **m** suffix only applies to **minutes**. Spec specifies that **m** can also be applied to **months**, but that would cause a conflict in syntax.
* **months** and **years** only available if dateutils is installed (relativedelta is used instead of timedelta).

## Misc

### with_fallback

- `with_fallback`: Usage: `config3 = config1.with_fallback(config2)` or `config3 = config1.with_fallback('samples/aws.conf')`

### from_dict

```python
d = OrderedDict()
d['banana'] = 3
d['apple'] = 4
d['pear'] = 1
d['orange'] = 2
config = ConfigFactory.from_dict(d)
assert config == d
```

## TODO

| Items                                             |       Status       |
| ------------------------------------------------- | :----------------: |
| Comments                                          | :white_check_mark: |
| Omit root braces                                  | :white_check_mark: |
| Key-value separator                               | :white_check_mark: |
| Commas                                            | :white_check_mark: |
| Whitespace                                        | :white_check_mark: |
| Duplicate keys and object merging                 | :white_check_mark: |
| Unquoted strings                                  | :white_check_mark: |
| Multi-line strings                                | :white_check_mark: |
| String value concatenation                        | :white_check_mark: |
| Array concatenation                               | :white_check_mark: |
| Object concatenation                              | :white_check_mark: |
| Arrays without commas                             | :white_check_mark: |
| Path expressions                                  | :white_check_mark: |
| Paths as keys                                     | :white_check_mark: |
| Substitutions                                     | :white_check_mark: |
| Self-referential substitutions                    | :white_check_mark: |
| The `+=` separator                                | :white_check_mark: |
| Includes                                          | :white_check_mark: |
| Include semantics: merging                        | :white_check_mark: |
| Include semantics: substitution                   | :white_check_mark: |
| Include semantics: missing files                  |        :x:         |
| Include semantics: file formats and extensions    |        :x:         |
| Include semantics: locating resources             |        :x:         |
| Include semantics: preventing cycles              |        :x:         |
| Conversion of numerically-index objects to arrays | :white_check_mark: |

| API Recommendations                               | Status |
| ------------------------------------------------- | :----: |
| Conversion of numerically-index objects to arrays |  :x:   |
| Automatic type conversions                        |  :x:   |
| Units format                                      |  :x:   |
| Duration format                                   |  :x:   |
| Size in bytes format                              |  :x:   |
| Config object merging and file merging            |  :x:   |
| Java properties mapping                           |  :x:   |

### Contributors

  - Aleksey Ostapenko ([@kbabka](https://github.com/kbakba))
  - Martynas Mickevičius ([@2m](https://github.com/2m))
  - Joe Halliwell ([@joehalliwell](https://github.com/joehalliwell))
  - Tasuku Okuda ([@okdtsk](https://github.com/okdtsk))
  - Uri Laserson ([@laserson](https://github.com/laserson))
  - Bastian Kuberek ([@bkuberek](https://github.com/bkuberek))
  - Varun Madiath ([@vamega](https://github.com/vamega))
  - Andrey Proskurnev ([@ariloulaleelay](https://github.com/ariloulaleelay))
  - Michael Overmeyer ([@movermeyer](https://github.com/movermeyer))
  - Virgil Palanciuc ([@virgil-palanciuc](https://github.com/virgil-palanciuc))
  - Douglas Simon ([@dougxc](https://github.com/dougxc))
  - Gilles Duboscq ([@gilles-duboscq](https://github.com/gilles-duboscq))
  - Stefan Anzinger ([@sanzinger](https://github.com/sanzinger))
  - Ryan Van Gilder ([@ryban](https://github.com/ryban))
  - Martin Kristiansen ([@lillekemiker](https://github.com/lillekemiker))
  - Yizheng Liao ([@yzliao](https://github.com/yzliao))
  - atomerju ([@atomerju](https://github.com/atomerju))
  - Nick Gerow ([@NickG123](https://github.com/NickG123))
  - jjtk88 ([@jjtk88](https://github.com/jjtk88))
  - Aki Ariga ([@chezou](https://github.com/chezou))
  - Joel Grus ([@joelgrus](https://github.com/joelgrus))
  - Anthony Alba [@aalba6675](https://github.com/aalba6675)
  - hugovk [@hugovk](https://github.com/hugovk)
  - chunyang-wen [@chunyang-wen](https://github.com/chunyang-wen)
  - afanasev [@afanasev](https://github.com/afanasev)
  - derkcrezee [@derkcrezee](https://github.com/derkcrezee)
  - Roee Nizan [@roee-allegro](https://github.com/roee-allegro)
  - Samuel Bible [@sambible](https://github.com/sambible)
  - Christophe Duong [@ChristopheDuong](https://github.com/ChristopheDuong)
  - lune* [@lune-sta](https://github.com/lune-sta)
  - Sascha [@ElkMonster](https://github.com/ElkMonster)
  - Tomas Witzany [@Tommassino](https://github.com/Tommassino)
  - Gabriel Shaar [@gabis-precog](https://github.com/gabis-precog)
  - Brandon Martin [@bdmartin](https://github.com/bdmartin)
  - Bryan Richter [@chreekat](https://github.com/chreekat)
  - dtarakanov1 [@dtarakanov](https://github.com/dtarakanov)
  - Anuj Kumar [@anujkumar93](https://github.com/anujkumar93)
  - Guillaume Poulin [@gpoulin](https://github.com/gpoulin)
  - Scott Johnson [@scottj97](https://github.com/scottj97)
  - Pablo Manso [@manso92](https://github.com/manso92)
  - Marc Rijken [@mrijken](https://github.com/mrijken)
  - Michel Rouly [@jrouly](https://github.com/jrouly)
  - Xing Hai Xu [@xinghaixu](https://github.com/xinghaixu)
  - Peter Zaitcev [@USSX-Hares](https://github.com/USSX-Hares)
  - Oliver Nemček [@olii](https://github.com/olii)
  - Guillaume George [@LysanderGG](https://github.com/LysanderGG)

### Thanks

  - Agnibha ([@agnibha](https://github.com/agnibha))
  - Ernest Mishkin ([@eric239](https://github.com/eric239))
  - Alexey Terentiev ([@alexey-terentiev](https://github.com/alexey-terentiev))
  - Prashant Shewale ([@pvshewale](https://github.com/pvshewale))
  - mh312 ([@mh321](https://github.com/mh321))
  - François Farquet ([@farquet](https://github.com/farquet))
  - Gavin Bisesi ([@Daenyth](https://github.com/Daenyth))
  - Cosmin Basca ([@cosminbasca](https://github.com/cosminbasca))
  - cryptofred ([@cryptofred](https://github.com/cryptofred))
  - Dominik1123 ([@Dominik1123](https://github.com/Dominik1123))
  - Richard Taylor ([@richard534](https://github.com/richard534))
  - Sergii Lutsanych ([@sergii1989](https://github.com/sergii1989))
