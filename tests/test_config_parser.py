# -*- encoding: utf-8 -*-

import json
import os
import tempfile
from collections import OrderedDict
from datetime import timedelta

from pyparsing import ParseBaseException, ParseException, ParseSyntaxException
import asset
import mock
import pytest
from pyhocon import (ConfigFactory, ConfigParser, ConfigSubstitutionException, ConfigTree)
from pyhocon.exceptions import (ConfigException, ConfigMissingException,
                                ConfigWrongTypeException)

try:
    from dateutil.relativedelta import relativedelta as period
except Exception:
    from datetime import timedelta as period


class TestConfigParser(object):
    def test_parse_simple_value(self):
        config = ConfigFactory.parse_string(
            """t = {
                c = 5
                "d" = true
                e.y = {
                    f: 7
                    g: "hey dude!"
                    h: hey man
                    i = \"\"\"
                        "first line"
                        "second" line
                        \"\"\"
                }
                j = [1, 2, 3]
                u = 192.168.1.3/32
                g = null
            }
            """
        )

        assert config.get_string('t.c') == '5'
        assert config.get_int('t.c') == 5
        assert config.get_float('t.c') == 5.0
        assert config.get('t.e.y.f') == 7
        assert config.get('t.e.y.g') == 'hey dude!'
        assert config.get('t.e.y.h') == 'hey man'
        assert [v.strip() for v in config.get('t.e.y.i').split('\n')] == ['', '"first line"', '"second" line', '']
        assert config.get_bool('t.d') is True
        assert config.get_int('t.e.y.f') == 7
        assert config.get('t.j') == [1, 2, 3]
        assert config.get('t.u') == '192.168.1.3/32'
        assert config.get_int('t.g') is None
        assert config.get_float('t.g') is None
        assert config.get_string('t.g') is None
        assert config.get_bool('t.g') is None
        assert config.get_list('t.g') is None
        assert config.get_config('t.g') is None

    @pytest.mark.parametrize('forbidden_char', ['+', '`', '^', '?', '!', '@', '*', '&'])
    def test_fail_parse_forbidden_characters(self, forbidden_char):
        with pytest.raises(ParseBaseException):
            ConfigFactory.parse_string('a: hey man{}'.format(forbidden_char))

    @pytest.mark.parametrize('forbidden_char', ['$', '"'])
    def test_fail_parse_forbidden_characters_in_context(self, forbidden_char):
        with pytest.raises(ParseException):
            ConfigFactory.parse_string('a: hey man{}'.format(forbidden_char))

    @pytest.mark.parametrize('forbidden_char', ['+', '`', '^', '?', '!', '@', '*', '&'])
    def test_parse_forbidden_characters_quoted(self, forbidden_char):
        value = "hey man{}".format(forbidden_char)
        config = ConfigFactory.parse_string('a: "{}"'.format(value))
        assert config.get_string("a") == value

    def test_parse_with_enclosing_brace(self):
        config = ConfigFactory.parse_string(
            """
            {
                a: {
                    b: 5
                }
            }
            """
        )

        assert config.get_string('a.b') == '5'

    @pytest.mark.parametrize('data_set', [
        ('a: 1 minutes', period(minutes=1)),
        ('a: 1minutes', period(minutes=1)),
        ('a: 2 minute', period(minutes=2)),
        ('a: 3 m', period(minutes=3)),
        ('a: 3m', period(minutes=3)),
        ('a: 3 min', '3 min'),

        ('a: 4 seconds', period(seconds=4)),
        ('a: 5 second', period(seconds=5)),
        ('a: 6 s', period(seconds=6)),
        ('a: 6 sec', '6 sec'),

        ('a: 7 hours', period(hours=7)),
        ('a: 8 hour', period(hours=8)),
        ('a: 9 h', period(hours=9)),

        ('a: 10 weeks', period(weeks=10)),
        ('a: 11 week', period(weeks=11)),
        ('a: 12 w', period(weeks=12)),

        ('a: 10 days', period(days=10)),
        ('a: 11 day', period(days=11)),
        ('a: 12 d', period(days=12)),

        ('a: 110 microseconds', period(microseconds=110)),
        ('a: 111 microsecond', period(microseconds=111)),
        ('a: 112 micros', period(microseconds=112)),
        ('a: 113 micro', period(microseconds=113)),
        ('a: 114 us', period(microseconds=114)),

        ('a: 110 milliseconds', timedelta(milliseconds=110)),
        ('a: 111 millisecond', timedelta(milliseconds=111)),
        ('a: 112 millis', timedelta(milliseconds=112)),
        ('a: 113 milli', timedelta(milliseconds=113)),
        ('a: 114 ms', timedelta(milliseconds=114)),

        ('a: 110 nanoseconds', period(microseconds=0)),
        ('a: 11000 nanoseconds', period(microseconds=11)),
        ('a: 1110000 nanosecond', period(microseconds=1110)),
        ('a: 1120000 nanos', period(microseconds=1120)),
        ('a: 1130000 nano', period(microseconds=1130)),
        ('a: 1140000 ns', period(microseconds=1140)),
    ])
    def test_parse_string_with_duration(self, data_set):
        config = ConfigFactory.parse_string(data_set[0])

        assert config['a'] == data_set[1]

    def test_parse_string_with_duration_with_long_unit_name(self):
        config = ConfigFactory.parse_string(
            """
            a: foo
            b: 10 weeks
            c: bar
            """
        )
        assert config['b'] == period(weeks=10)

    def test_parse_with_enclosing_square_bracket(self):
        config = ConfigFactory.parse_string("[1, 2, 3]")
        assert config == [1, 2, 3]

    def test_quoted_key_with_dots(self):
        config = ConfigFactory.parse_string(
            """
            "a.b.c.d": 3
            t {
              "d": {
                "c": 5
              }
            }
            k {
                "b.f.d": 7
            }
            """
        )
        assert config['"a.b.c.d"'] == 3
        assert config['t.d.c'] == 5
        assert config['k."b.f.d"'] == 7

    def test_dotted_notation_merge(self):
        config = ConfigFactory.parse_string(
            """
            a {
                b = foo
                c = bar
            }
            a.c = ${a.b}" "${a.b}
            a.d = baz
            """
        )
        assert config['a.b'] == "foo"
        assert config['a.c'] == "foo foo"
        assert config['a.d'] == "baz"

    def test_comma_to_separate_expr(self):
        config = ConfigFactory.parse_string(
            """
            a=1,
            b="abc",
            c=the man,
            d=woof,
            a-b-c-d=test,
            a b c d=test2,
            "a b c d e"=test3
            """
        )
        assert config.get('a') == 1
        assert config.get('b') == 'abc'
        assert config.get('c') == 'the man'
        assert config.get('d') == 'woof'
        assert config.get('a-b-c-d') == 'test'
        assert config.get('a b c d') == 'test2'
        assert config.get('a b c d e') == 'test3'

    def test_dict_merge(self):
        config = ConfigFactory.parse_string(
            """
            a {
                    d {
                            g.h.j.u: 5
                            g {
                                    h.d: 4
                            }
                            g.h.k: f d
                    }

                    h.i.m = 7
                    h.i {
                            d: 5
                    }

                    h.i {
                            e:65
                    }
            }
            """)

        expected_result = {
            "a": {
                "d": {
                    "g": {
                        "h": {
                            "j": {
                                "u": 5
                            },
                            "d": 4,
                            "k": "f d"
                        }
                    }
                },
                "h": {
                    "i": {
                        "m": 7,
                        "d": 5,
                        "e": 65
                    }
                }
            }
        }
        assert expected_result == config

    def test_parse_with_comments(self):
        config = ConfigFactory.parse_string(
            """
            // comment 1
            # comment 2
            {
                c = test   // comment 0
                g = 6 test   # comment 0
                # comment 3
                a: { # comment 4
                    b: test,                # comment 5
                } # comment 6
                t = [1, # comment 7
                     2, # comment 8
                     3, # comment 9
                ]
            } # comment 10
            // comment 11
            // comment 12
            """
        )

        assert config.get('c') == 'test'
        assert config.get('g') == '6 test'
        assert config.get('a.b') == 'test'
        assert config.get_string('a.b') == 'test'
        assert config.get('t') == [1, 2, 3]

    def test_missing_config(self):
        config = ConfigFactory.parse_string(
            """
            a = 5
            """
        )
        # b is not set so show raise an exception
        with pytest.raises(ConfigMissingException):
            config.get('b')

    def test_parse_null(self):
        config = ConfigFactory.parse_string(
            """
            a = null
            b = [null]
            """
        )
        assert config.get('a') is None
        assert config.get('b')[0] is None

    def test_parse_override(self):
        config = ConfigFactory.parse_string(
            """
            {
                a: {
                    b: {
                        c = 5
                    }
                }
                a.b {
                    c = 7
                    d = 8
                }
            }
            """
        )

        assert config.get('a.b.c') == 7
        assert config.get('a.b.d') == 8

    def test_concat_dict(self):
        config = ConfigFactory.parse_string(
            """
            a: {b: 1}
            a: {c: 2}
            b: {c: 3} {d: 4} {
                c: 5
            }
            """
        )
        assert config.get('a.b') == 1
        assert config.get('a.c') == 2
        assert config.get('b.c') == 5
        assert config.get('b.d') == 4

    def test_concat_string(self):
        config = ConfigFactory.parse_string(
            """
            a = a b c
            b = 5 b
            c = b 7
            """
        )

        assert config.get('a') == 'a b c'
        assert config.get('b') == '5 b'
        assert config.get('c') == 'b 7'

    def test_concat_list(self):
        config = ConfigFactory.parse_string(
            """
            a = [1, 2] [3, 4] [
              5,
              6
            ]
            """
        )

        assert config.get('a') == [1, 2, 3, 4, 5, 6]
        assert config.get_list('a') == [1, 2, 3, 4, 5, 6]

    def test_bad_concat(self):
        ConfigFactory.parse_string('a = 45\n')
        with pytest.raises(ConfigWrongTypeException):
            ConfigFactory.parse_string('a = [4] "4"')
        with pytest.raises(ConfigWrongTypeException):
            ConfigFactory.parse_string('a = "4" [5]')
        with pytest.raises(ConfigWrongTypeException):
            ConfigFactory.parse_string('a = {b: 5} "4"')

    def test_string_substitutions(self):
        config1 = ConfigFactory.parse_string(
            """
            {
                a: {
                    b: {
                        c = str
                        e = "str      "
                    }
                }
                d = ${a.b.c}
                f = ${a.b.e}
            }
            """
        )

        assert config1.get('a.b.c') == 'str'
        assert config1.get('d') == 'str'
        assert config1.get('f') == 'str      '

        config2 = ConfigFactory.parse_string(
            """
            {
                a: {
                    b: {
                        c = str
                        e = "str      "
                    }
                }
                d = test  ${a.b.c}
                f = test  ${a.b.e}
            }
            """
        )

        assert config2.get('a.b.c') == 'str'
        assert config2.get('d') == 'test  str'
        assert config2.get('f') == 'test  str      '

        config3 = ConfigFactory.parse_string(
            u"""
            {
                a: {
                    b: {
                        c = str
                        e = "str      "
                    }
                }
                d = test  ${a.b.c}  me
                f = test  ${a.b.e}  me
            }
            """
        )

        assert config3.get('a.b.c') == 'str'
        assert config3.get('d') == 'test  str  me'
        assert config3.get('f') == 'test  str        me'

    def test_string_substitutions_with_no_space(self):
        config = ConfigFactory.parse_string(
            """
                app.heap_size = 128
                app.java_opts = [
                    -Xms${app.heap_size}m
                    -Xmx${app.heap_size}m
                ]
            """
        )

        assert config.get('app.java_opts') == [
            '-Xms128m',
            '-Xmx128m'
        ]

    def test_int_substitutions(self):
        config1 = ConfigFactory.parse_string(
            """
            {
                a: {
                    b: {
                        c = 5
                    }
                }
                d = ${a.b.c}
            }
            """
        )

        assert config1.get('a.b.c') == 5
        assert config1.get('d') == 5

        config2 = ConfigFactory.parse_string(
            """
            {
                a: {
                    b: {
                        c = 5
                    }
                }
                d = test ${a.b.c}
            }
            """
        )

        assert config2.get('a.b.c') == 5
        assert config2.get('d') == 'test 5'

        config3 = ConfigFactory.parse_string(
            """
            {
                a: {
                    b: {
                        c = 5
                    }
                }
                d = test ${a.b.c} me
            }
            """
        )

        assert config3.get('a.b.c') == 5
        assert config3.get('d') == 'test 5 me'

    def test_cascade_string_substitutions(self):
        config = ConfigFactory.parse_string(
            """
            {
                a: {
                    b: {
                        c = ${e}
                    }
                }
                d = test ${a.b.c} me
                e = 7
            }
            """
        )

        assert config.get('a.b.c') == 7
        assert config.get('d') == 'test 7 me'

    def test_multiple_substitutions(self):
        config = ConfigFactory.parse_string(
            """
                a = 5
                b=${a}${a}
                c=${a} ${a}
            """
        )

        assert config == {
            'a': 5,
            'b': '55',
            'c': '5 5'
        }

    def test_dict_substitutions(self):
        config = ConfigFactory.parse_string(
            """
                data-center-generic = { cluster-size = 6 }
                data-center-east = ${data-center-generic} {name = "east"}
            """
        )

        assert config.get('data-center-east.cluster-size') == 6
        assert config.get('data-center-east.name') == 'east'

        config2 = ConfigFactory.parse_string(
            """
                data-center-generic = { cluster-size = 6 }
                data-center-east = {name = "east"} ${data-center-generic}
            """
        )

        assert config2.get('data-center-east.cluster-size') == 6
        assert config2.get('data-center-east.name') == 'east'

        config3 = ConfigFactory.parse_string(
            """
                data-center-generic = { cluster-size = 6 }
                data-center-east = {name = "east"} ${data-center-generic} { cluster-size = 9, opts = "-Xmx4g" }
            """
        )

        assert config3.get('data-center-east.cluster-size') == 9
        assert config3.get('data-center-east.name') == 'east'
        assert config3.get('data-center-east.opts') == '-Xmx4g'

        config4 = ConfigFactory.parse_string(
            """
                data-center-generic = { cluster-size = 6 }
                data-center-east = {name = "east"} ${data-center-generic}
                data-center-east-prod = ${data-center-east} {tmpDir=/tmp}
            """
        )

        assert config4.get('data-center-east.cluster-size') == 6
        assert config4.get('data-center-east.name') == 'east'
        assert config4.get('data-center-east-prod.cluster-size') == 6
        assert config4.get('data-center-east-prod.tmpDir') == '/tmp'

        config5 = ConfigFactory.parse_string(
            """
                data-center-generic = { cluster-size = 6 }
                data-center-east = ${data-center-generic}
                data-center-east = { name = "east" }
            """
        )

        assert config5['data-center-east'] == {
            'name': 'east',
            'cluster-size': 6
        }

        config6 = ConfigFactory.parse_string(
            """
                data-center-generic = { cluster-size = 6 }
                data-center-east = { name = "east" }
                data-center-east = ${data-center-generic}
            """
        )
        assert config6['data-center-east'] == {
            'name': 'east',
            'cluster-size': 6
        }

    def test_dos_chars_with_unquoted_string_noeol(self):
        config = ConfigFactory.parse_string("foo = bar")
        assert config['foo'] == 'bar'

    def test_dos_chars_with_quoted_string_noeol(self):
        config = ConfigFactory.parse_string('foo = "5"')
        assert config['foo'] == '5'

    def test_dos_chars_with_triple_quoted_string_noeol(self):
        config = ConfigFactory.parse_string('foo = """5"""')
        assert config['foo'] == '5'

    def test_dos_chars_with_int_noeol(self):
        config = ConfigFactory.parse_string("foo = 5")
        assert config['foo'] == 5

    def test_dos_chars_with_float_noeol(self):
        config = ConfigFactory.parse_string("foo = 5.0")
        assert config['foo'] == 5.0

    def test_list_substitutions(self):
        config = ConfigFactory.parse_string(
            """
                common_modules = [php, python]
                host_modules = ${common_modules} [java]
            """
        )

        assert config.get('host_modules') == ['php', 'python', 'java']

        config2 = ConfigFactory.parse_string(
            """
                common_modules = [php, python]
                host_modules = [java] ${common_modules}
            """
        )

        assert config2.get('host_modules') == ['java', 'php', 'python']

        config3 = ConfigFactory.parse_string(
            """
                common_modules = [php, python]
                host_modules = [java] ${common_modules} [perl]
            """
        )

        assert config3.get('common_modules') == ['php', 'python']
        assert config3.get('host_modules') == ['java', 'php', 'python', 'perl']

        config4 = ConfigFactory.parse_string(
            """
                common_modules = [php, python]
                host_modules = [java] ${common_modules} [perl]
                full_modules = ${host_modules} [c, go]
            """
        )

        assert config4.get('common_modules') == ['php', 'python']
        assert config4.get('host_modules') == ['java', 'php', 'python', 'perl']
        assert config4.get('full_modules') == ['java', 'php', 'python', 'perl', 'c', 'go']

    def test_list_element_substitution(self):
        config = ConfigFactory.parse_string(
            """
                main_language = php
                languages = [java, ${main_language}]
            """
        )

        assert config.get('languages') == ['java', 'php']

    def test_substitution_list_with_append(self):
        config = ConfigFactory.parse_string(
            """
            application.foo = 128mm
            application.large-jvm-opts = ["-XX:+UseParNewGC"] [-Xm16g, ${application.foo}]
            application.large-jvm-opts2 = [-Xm16g, ${application.foo}] ["-XX:+UseParNewGC"]
            """)

        assert config["application.large-jvm-opts"] == [
            '-XX:+UseParNewGC',
            '-Xm16g',
            '128mm'
        ]

        assert config["application.large-jvm-opts2"] == [
            '-Xm16g',
            '128mm',
            '-XX:+UseParNewGC',
        ]

    def test_substitution_list_with_append_substitution(self):
        config = ConfigFactory.parse_string(
            """
            application.foo = 128mm
            application.default-jvm-opts = ["-XX:+UseParNewGC"]
            application.large-jvm-opts = ${application.default-jvm-opts} [-Xm16g, ${application.foo}]
            application.large-jvm-opts2 = [-Xm16g, ${application.foo}] ${application.default-jvm-opts}
            """)

        assert config["application.large-jvm-opts"] == [
            '-XX:+UseParNewGC',
            '-Xm16g',
            '128mm'
        ]

        assert config["application.large-jvm-opts2"] == [
            '-Xm16g',
            '128mm',
            '-XX:+UseParNewGC'
        ]

    def test_non_existent_substitution(self):
        with pytest.raises(ConfigSubstitutionException):
            ConfigFactory.parse_string(
                """
                    common_modules = ${non_existent}
                """
            )

        with pytest.raises(ConfigSubstitutionException):
            ConfigFactory.parse_string(
                """
                    common_modules = abc ${non_existent}
                """
            )

        with pytest.raises(ConfigSubstitutionException):
            ConfigFactory.parse_string(
                """
                    common_modules = ${non_existent} abc
                """
            )

        with pytest.raises(ConfigSubstitutionException):
            ConfigFactory.parse_string(
                """
                    common_modules = abc ${non_existent} def
                """
            )

    def test_non_compatible_substitution(self):
        with pytest.raises(ConfigWrongTypeException):
            ConfigFactory.parse_string(
                """
                    common_modules = [perl]
                    host_modules = 55 ${common_modules}
                """
            )

        with pytest.raises(ConfigWrongTypeException):
            ConfigFactory.parse_string(
                """
                    common_modules = [perl]
                    host_modules = ${common_modules} 55
                """
            )

        with pytest.raises(ConfigWrongTypeException):
            ConfigFactory.parse_string(
                """
                    common_modules = [perl]
                    host_modules = aa ${common_modules} bb
                """
            )

        with pytest.raises(ConfigWrongTypeException):
            ConfigFactory.parse_string(
                """
                    common_modules = [perl]
                    host_modules = aa ${common_modules}
                """
            )

        with pytest.raises(ConfigWrongTypeException):
            ConfigFactory.parse_string(
                """
                    common_modules = [perl]
                    host_modules = ${common_modules} aa
                """
            )

        with pytest.raises(ConfigWrongTypeException):
            ConfigFactory.parse_string(
                """
                    common_modules = [perl]
                    host_modules = aa ${common_modules} bb
                """
            )

    def test_self_ref_substitution_array(self):
        config = ConfigFactory.parse_string(
            """
            x = [1,2]
            x = ${x} [3,4]
            x = [-1, 0] ${x} [5, 6]
            x = [-3, -2] ${x}
            """
        )
        assert config.get("x") == [-3, -2, -1, 0, 1, 2, 3, 4, 5, 6]

    def test_self_append_array(self):
        config = ConfigFactory.parse_string(
            """
            x = [1,2]
            x += [3,4]
            """
        )
        assert config.get("x") == [1, 2, 3, 4]

    def test_self_append_string(self):
        '''
        Should be equivalent to
        x = abc
        x = ${?x} def
        '''
        config = ConfigFactory.parse_string(
            """
            x = abc
            x += def
            """
        )
        assert config.get("x") == "abc def"

    def test_self_append_non_existent_string(self):
        '''
        Should be equivalent to x = ${?x} def
        '''
        config = ConfigFactory.parse_string(
            """
            x += def
            """
        )
        assert config.get("x") == " def"

    def test_self_append_nonexistent_array(self):
        config = ConfigFactory.parse_string(
            """
            x += [1,2]
            """
        )
        assert config.get("x") == [1, 2]

    def test_self_append_object(self):
        config = ConfigFactory.parse_string(
            """
            x = {a: 1}
            x += {b: 2}
            """
        )
        assert config.get("x") == {'a': 1, 'b': 2}

    def test_self_append_nonexistent_object(self):
        config = ConfigFactory.parse_string(
            """
            x += {a: 1}
            """
        )
        assert config.get("x") == {'a': 1}

    def test_self_ref_substitution_array_to_dict(self):
        config = ConfigFactory.parse_string(
            """
            x = [1,2]
            x = {x: [3,4]}
            x = {y: [5,6]}
            x = {z: ${x}}
            """
        )
        assert config.get("x.x") == [3, 4]
        assert config.get("x.y") == [5, 6]
        assert config.get("x.z") == {'x': [3, 4], 'y': [5, 6]}

    def test_self_ref_substitiotion_dict_in_array(self):
        config = ConfigFactory.parse_string(
            """
            x = {x: [3,4]}
            x = [${x}, 2, 3]
            """
        )
        (one, two, three) = config.get("x")
        assert one == {'x': [3, 4]}
        assert two == 2
        assert three == 3

    def test_self_ref_substitution_dict_path(self):
        config = ConfigFactory.parse_string(
            """
            x = {y: {z: 1}}
            x = ${x.y}
            """
        )
        assert config.get("x.y") == {'z': 1}
        assert config.get("x.z") == 1
        assert set(config.get("x").keys()) == set(['y', 'z'])

    def test_self_ref_substitution_dict_path_hide(self):
        config = ConfigFactory.parse_string(
            """
            x = {y: {y: 1}}
            x = ${x.y}
            """
        )
        assert config.get("x.y") == 1
        assert set(config.get("x").keys()) == set(['y'])

    def test_self_ref_substitution_dict_recurse(self):
        with pytest.raises(ConfigSubstitutionException):
            ConfigFactory.parse_string(
                """
                x = ${x}
                """
            )

    def test_self_ref_substitution_dict_recurse2(self):
        with pytest.raises(ConfigSubstitutionException):
            ConfigFactory.parse_string(
                """
                x = ${x}
                x = ${x}
                """
            )

    def test_self_ref_substitution_dict_merge(self):
        '''
        Example from HOCON spec
        '''
        config = ConfigFactory.parse_string(
            """
            foo : { a : { c : 1 } }
            foo : ${foo.a}
            foo : { a : 2 }
            """
        )
        assert config.get('foo') == {'a': 2, 'c': 1}
        assert set(config.keys()) == set(['foo'])

    def test_self_ref_substitution_dict_otherfield(self):
        '''
        Example from HOCON spec
        '''
        config = ConfigFactory.parse_string(
            """
            bar : {
              foo : 42,
              baz : ${bar.foo}
            }
            """
        )
        assert config.get("bar") == {'foo': 42, 'baz': 42}
        assert set(config.keys()) == set(['bar'])

    def test_self_ref_substitution_dict_otherfield_merged_in(self):
        '''
        Example from HOCON spec
        '''
        config = ConfigFactory.parse_string(
            """
            bar : {
                foo : 42,
                baz : ${bar.foo}
            }
            bar : { foo : 43 }
            """
        )
        assert config.get("bar") == {'foo': 43, 'baz': 43}
        assert set(config.keys()) == set(['bar'])

    def test_self_ref_substitution_dict_otherfield_merged_in_mutual(self):
        '''
        Example from HOCON spec
        '''
        config = ConfigFactory.parse_string(
            """
            // bar.a should end up as 4
            bar : { a : ${foo.d}, b : 1 }
            bar.b = 3
            // foo.c should end up as 3
            foo : { c : ${bar.b}, d : 2 }
            foo.d = 4
            """
        )
        assert config.get("bar") == {'a': 4, 'b': 3}
        assert config.get("foo") == {'c': 3, 'd': 4}
        assert set(config.keys()) == set(['bar', 'foo'])

    def test_self_ref_substitution_string_opt_concat(self):
        '''
        Example from HOCON spec
        '''
        config = ConfigFactory.parse_string(
            """
            a = ${?a}foo
            """
        )
        assert config.get("a") == 'foo'
        assert set(config.keys()) == set(['a'])

    def test_self_ref_substitution_dict_recurse_part(self):
        with pytest.raises(ConfigSubstitutionException):
            ConfigFactory.parse_string(
                """
                x = ${x} {y: 1}
                x = ${x.y}
                """
            )

    def test_self_ref_substitution_object(self):
        config = ConfigFactory.parse_string(
            """
            x = {a: 1, b: 2}
            x = ${x} {c: 3}
            x = {z: 0} ${x}
            x = {y: -1} ${x} {d: 4}
            """
        )
        assert config.get("x") == {'a': 1, 'b': 2, 'c': 3, 'z': 0, 'y': -1, 'd': 4}

    def test_self_ref_child(self):
        config = ConfigFactory.parse_string(
            """
                a.b = 3
                a.b = ${a.b}
                a.b = ${a.b}
                a.c = [1,2]
                a.c = ${a.c}
                a.d = {foo: bar}
                a.d = ${a.d}

            """
        )
        assert config.get("a") == {'b': 3, 'c': [1, 2], 'd': {'foo': 'bar'}}

    def test_concat_multi_line_string(self):
        config = ConfigFactory.parse_string(
            """
                common_modules = perl \
                java \
                python
            """
        )

        assert [x.strip() for x in config['common_modules'].split() if x.strip(' ') != ''] == ['perl', 'java', 'python']

    def test_concat_multi_line_list(self):
        config = ConfigFactory.parse_string(
            """
                common_modules = [perl] \
                [java] \
                [python]
            """
        )

        assert config['common_modules'] == ['perl', 'java', 'python']

    def test_concat_multi_line_dict(self):
        config = ConfigFactory.parse_string(
            """
                common_modules = {a:perl} \
                {b:java} \
                {c:python}
            """
        )

        assert config['common_modules'] == {'a': 'perl', 'b': 'java', 'c': 'python'}

    def test_parse_URL_from_samples(self):
        config = ConfigFactory.parse_URL("file:samples/aws.conf")
        assert config.get('data-center-generic.cluster-size') == 6
        assert config.get('large-jvm-opts') == ['-XX:+UseParNewGC', '-Xm16g']

    def test_parse_URL_from_invalid(self):
        config = ConfigFactory.parse_URL("https://nosuchurl")
        assert config == []

    def test_include_dict_from_samples(self):
        config = ConfigFactory.parse_file("samples/animals.conf")
        assert config.get('cat.garfield.say') == 'meow'
        assert config.get('dog.mutt.hates.garfield.say') == 'meow'

    def test_include_glob_dict_from_samples(self):
        config = ConfigFactory.parse_file("samples/all_animals.conf")
        assert config.get('animals.garfield.say') == 'meow'
        assert config.get('animals.mutt.hates.garfield.say') == 'meow'

    def test_include_glob_list_from_samples(self):
        config = ConfigFactory.parse_file("samples/all_bars.conf")
        bars = config.get_list('bars')
        assert len(bars) == 10

        names = {bar['name'] for bar in bars}
        types = {bar['type'] for bar in bars if 'type' in bar}
        print(types, '(((((')
        assert 'Bloody Mary' in names
        assert 'Homer\'s favorite coffee' in names
        assert 'milk' in types

    def test_list_of_dicts(self):
        config = ConfigFactory.parse_string(
            """
            a: [
                {a: 1, b: 2},
                {a: 3, c: 4},
            ]
            """
        )
        assert config['a'] == [
            {'a': 1, 'b': 2},
            {'a': 3, 'c': 4}
        ]

    def test_list_of_lists(self):
        config = ConfigFactory.parse_string(
            """
            a: [
                [1, 2]
                [3, 4]
            ]
            """
        )
        assert config['a'] == [
            [1, 2],
            [3, 4]
        ]

    def test_list_of_dicts_with_merge(self):
        config = ConfigFactory.parse_string(
            """
            b = {f: 4}
            a: [
                ${b} {a: 1, b: 2},
                {a: 3, c: 4} ${b},
                {a: 3} ${b} {c: 6},
            ]
            """
        )
        assert config['a'] == [
            {'a': 1, 'b': 2, 'f': 4},
            {'a': 3, 'c': 4, 'f': 4},
            {'a': 3, 'c': 6, 'f': 4}
        ]

    def test_list_of_lists_with_merge(self):
        config = ConfigFactory.parse_string(
            """
            b = [5, 6]
            a: [
                ${b} [1, 2]
                [3, 4] ${b}
                [1, 2] ${b} [7, 8]
            ]
            """
        )
        assert config['a'] == [
            [5, 6, 1, 2],
            [3, 4, 5, 6],
            [1, 2, 5, 6, 7, 8]
        ]

    def test_invalid_assignment(self):
        with pytest.raises(ParseSyntaxException):
            ConfigFactory.parse_string('common_modules [perl]')

        with pytest.raises(ParseException):
            ConfigFactory.parse_string('common_modules {} {perl: 1}')

        with pytest.raises(ParseSyntaxException):
            ConfigFactory.parse_string(
                """
                a = {f: 5}
                common_modules ${a} {perl: 1}
                """)

    def test_invalid_dict(self):
        with pytest.raises(ParseSyntaxException):
            ConfigFactory.parse_string(
                """
                a = {
                    f: 5
                    g
                }
                """)

        with pytest.raises(ParseSyntaxException):
            ConfigFactory.parse_string('a = {g}')

    def test_include_file(self):
        with tempfile.NamedTemporaryFile('w') as fdin:
            fdin.write('[1, 2]')
            fdin.flush()

            config1 = ConfigFactory.parse_string(
                """
                a: [
                    include "{tmp_file}"
                ]
                """.format(tmp_file=fdin.name)
            )
            assert config1['a'] == [1, 2]

            config2 = ConfigFactory.parse_string(
                """
                a: [
                    include file("{tmp_file}")
                ]
                """.format(tmp_file=fdin.name)
            )
            assert config2['a'] == [1, 2]

            config3 = ConfigFactory.parse_string(
                """
                a: [
                    include url("file://{tmp_file}")
                ]
                """.format(tmp_file=fdin.name)
            )
            assert config3['a'] == [1, 2]

    def test_include_missing_file(self):
        config1 = ConfigFactory.parse_string(
            """
            a: [
                include "dummy.txt"
                3
                4
            ]
            """
        )
        assert config1['a'] == [3, 4]

    def test_include_required_file(self):
        config = ConfigFactory.parse_string(
            """
            a {
                include required("samples/animals.d/cat.conf")
                t = 2
            }
            """
        )
        expected = {
            'a': {
                'garfield': {
                    'say': 'meow'
                },
                't': 2
            }
        }
        assert expected == config

        config2 = ConfigFactory.parse_string(
            """
            a {
                include required(file("samples/animals.d/cat.conf"))
                t = 2
            }
            """
        )
        assert expected == config2

    def test_include_missing_required_file(self):
        with pytest.raises(IOError):
            ConfigFactory.parse_string(
                """
                a: [
                    include required("dummy.txt")
                    3
                    4
                ]
                """
            )

    def test_include_asset_file(self, monkeypatch):
        with tempfile.NamedTemporaryFile('w') as fdin:
            fdin.write('{a: 1, b: 2}')
            fdin.flush()

            def load(*args, **kwargs):
                class File(object):
                    def __init__(self, filename):
                        self.filename = filename

                return File(fdin.name)

            monkeypatch.setattr(asset, "load", load)

            config = ConfigFactory.parse_string(
                """
                include package("dotted.name:asset/config_file")
                """
            )
            assert config['a'] == 1

    def test_include_dict(self):
        expected_res = {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4
        }
        with tempfile.NamedTemporaryFile('w') as fdin:
            fdin.write('{a: 1, b: 2}')
            fdin.flush()

            config1 = ConfigFactory.parse_string(
                """
                a: {{
                    include "{tmp_file}"
                    c: 3
                    d: 4
                }}
                """.format(tmp_file=fdin.name)
            )
            assert config1['a'] == expected_res

            config2 = ConfigFactory.parse_string(
                """
                a: {{
                    c: 3
                    d: 4
                    include "{tmp_file}"
                }}
                """.format(tmp_file=fdin.name)
            )
            assert config2['a'] == expected_res

            config3 = ConfigFactory.parse_string(
                """
                a: {{
                    c: 3
                    include "{tmp_file}"
                    d: 4
                }}
                """.format(tmp_file=fdin.name)
            )
            assert config3['a'] == expected_res

    def test_include_substitution(self):
        with tempfile.NamedTemporaryFile('w') as fdin:
            fdin.write('y = ${x}')
            fdin.flush()

            config = ConfigFactory.parse_string(
                """
                include "{tmp_file}"
                x = 42
                """.format(tmp_file=fdin.name)
            )
            assert config['x'] == 42
            assert config['y'] == 42

    @pytest.mark.xfail
    def test_include_substitution2(self):
        with tempfile.NamedTemporaryFile('w') as fdin:
            fdin.write('{ x : 10, y : ${x} }')
            fdin.flush()

            config = ConfigFactory.parse_string(
                """
                {
                    a : { include """ + '"' + fdin.name + """" }
                    a : { x : 42 }
                }
                """
            )
            assert config['a']['x'] == 42
            assert config['a']['y'] == 42

    def test_var_with_include_keyword(self):
        config = ConfigFactory.parse_string(
            """
            include-database=true
            """)

        assert config == {
            'include-database': True
        }

    def test_substitution_override(self):
        config = ConfigFactory.parse_string(
            """
            database {
                host = localhost
                port = 5432
                user = people
                name = peopledb
                pass = peoplepass
            }

            user=test_user
            pass=test_pass

            database {
                user = ${user}
                pass = ${pass}
            }

            """)

        assert config['database.user'] == 'test_user'
        assert config['database.pass'] == 'test_pass'

    def test_substitution_flat_override(self):
        config = ConfigFactory.parse_string(
            """
            database {
                name = peopledb
                pass = peoplepass
                name = ${?NOT_EXISTS}
                pass = ${?NOT_EXISTS}
            }
            """)

        assert config['database.name'] == 'peopledb'
        assert config['database.pass'] == 'peoplepass'

    def test_substitution_nested_override(self):
        config = ConfigFactory.parse_string(
            """
            database {
                name = peopledb
                pass = peoplepass
            }

            database {
                name = ${?user}
                pass = ${?pass}
            }

            """)

        assert config['database.name'] == 'peopledb'
        assert config['database.pass'] == 'peoplepass'

    def test_optional_with_merge(self):
        unresolved = ConfigFactory.parse_string(
            """
            foo: 42
            foo: ${?a}
            """, resolve=False)
        source = ConfigFactory.parse_string(
            """
            b: 14
            """)
        config = unresolved.with_fallback(source)
        assert config['foo'] == 42
        config = source.with_fallback(unresolved)
        assert config['foo'] == 42

    def test_fallback_with_resolve(self):
        config3 = ConfigFactory.parse_string("c=5")
        config2 = ConfigFactory.parse_string("b=${c}", resolve=False)
        config1 = ConfigFactory.parse_string("a=${b}", resolve=False) \
            .with_fallback(config2, resolve=False) \
            .with_fallback(config3)
        assert {'a': 5, 'b': 5, 'c': 5} == config1

    def test_optional_substitution(self):
        config = ConfigFactory.parse_string(
            """
            a = 45
            b = ${?c}
            d = ${?c} 4
            e = ${?a}
            g = ${?c1} ${?c2}
            h = ${?c1} ${?c2} 1
            """)

        assert 'b' not in config
        assert config['d'] == 4
        assert config['e'] == 45
        assert 'g' not in config
        assert config['h'] == 1

    def test_cascade_optional_substitution(self):
        config = ConfigFactory.parse_string(
            """
              num = 3
              retries_msg = You have ${num} retries
              retries_msg = ${?CUSTOM_MSG}
            """)
        assert config == {
            'num': 3,
            'retries_msg': 'You have 3 retries'
        }

    def test_substitution_cycle(self):
        with pytest.raises(ConfigSubstitutionException):
            ConfigFactory.parse_string(
                """
                a = ${b}
                b = ${c}
                c = ${a}
                """)

    def test_assign_number_with_eol(self):
        config = ConfigFactory.parse_string(
            """
            a =
            4

            b = # test
            # test2
            5

            c =

            6
            """
        )
        assert config['a'] == 4
        assert config['b'] == 5
        assert config['c'] == 6

    def test_assign_int(self):
        config = ConfigFactory.parse_string(
            """
            short = 12
            long = 12321321837612378126213217321
            negative = -15
            """
        )

        # on python 3 long will be an int but on python 2 long with be a long
        assert config['short'] == 12
        assert isinstance(config['short'], int)
        assert config['long'] == 12321321837612378126213217321
        assert isinstance(config['negative'], int)
        assert config['negative'] == -15

    def test_assign_float(self):
        config = ConfigFactory.parse_string(
            """
            a = 121.22
            b = -121.22
            c = .54
            d = -.54
            """
        )

        # on python 3 long will be an int but on python 2 long with be a long
        assert config['a'] == 121.22
        assert config['b'] == -121.22
        assert config['c'] == .54
        assert config['d'] == -.54

    def test_sci_real(self):
        """
        Test scientific expression of number
        """

        config = ConfigFactory.parse_string(
            """
            short = 12.12321
            long1 = 121.22E3423432
            neg_long1 = 121.22E-1
            long2 = 121.22e3423432
            neg_long2 = 121.22e-3
            """
        )

        # on python 3 long will be an int but on python 2 long with be a long
        assert config['short'] == 12.12321

        assert config['long1'] == 121.22E3423432
        assert config['neg_long1'] == 121.22E-1

        assert config['long2'] == 121.22E3423432
        assert config['neg_long2'] == 121.22E-3

    def test_assign_strings_with_eol(self):
        config = ConfigFactory.parse_string(
            """
            a =
            "a"

            b = # test
            # test2
            "b"

            c =

            "c"
            """
        )
        assert config['a'] == 'a'
        assert config['b'] == 'b'
        assert config['c'] == 'c'

    def test_assign_list_numbers_with_eol(self):
        config = ConfigFactory.parse_string(
            """
            a =
            [
            1,
            2,
            ]

            b = # test
            # test2
            [
            3,
            4,]

            c =

            [
            5,
            6
            ]
            """
        )
        assert config['a'] == [1, 2]
        assert config['b'] == [3, 4]
        assert config['c'] == [5, 6]

    def test_assign_list_strings_with_eol(self):
        config = ConfigFactory.parse_string(
            """
            a =
            [
            "a",
            "b",
            ]

            b = # test
            # test2
            [
            "c",
            "d",]

            c =

            [
            "e",
            "f"
            ]
            """
        )
        assert config['a'] == ['a', 'b']
        assert config['b'] == ['c', 'd']
        assert config['c'] == ['e', 'f']

    def test_assign_dict_strings_with_equal_sign_with_eol(self):
        config = ConfigFactory.parse_string(
            """
            a =
            {
            a: 1,
            b: 2,
            }

            b = # test
            # test2
            {
            c: 3,
            d: 4,}

            c =

            {
            e: 5,
            f: 6
            }
            """
        )
        assert config['a'] == {'a': 1, 'b': 2}
        assert config['b'] == {'c': 3, 'd': 4}
        assert config['c'] == {'e': 5, 'f': 6}

    def test_assign_dict_strings_no_equal_sign_with_eol(self):
        config = ConfigFactory.parse_string(
            """
            a
            {
            a: 1,
            b: 2,
            }

            b # test
            # test2
            {
            c: 3,
            d: 4,}

            c

            {
            e: 5,
            f: 6
            }
            """
        )
        assert config['a'] == {'a': 1, 'b': 2}
        assert config['b'] == {'c': 3, 'd': 4}
        assert config['c'] == {'e': 5, 'f': 6}

    def test_substitutions_overwrite(self):
        config1 = ConfigFactory.parse_string(
            """
            a = 123
            a = ${?test}
            a = 5
            """
        )

        assert config1['a'] == 5

        config2 = ConfigFactory.parse_string(
            """
            {
              database {
                host = "localhost"
                port = 8000
                url = ${database.host}":"${database.port}
              }

              database {
                host = ${?DB_HOST}
              }

              database {
                host = "other.host.net"
                port = 433
              }
            }
            """
        )

        assert config2['database']['host'] == 'other.host.net'
        assert config2['database']['port'] == 433
        assert config2['database']['url'] == 'other.host.net:433'

    def test_fallback_substitutions_overwrite(self):
        config1 = ConfigFactory.parse_string(
            """
            a = {
                b: 1
                c: 2
            }
            """
        )

        config2 = ConfigFactory.parse_string(
            """
            a.b = 4
            a.d = 3
            """
        )

        config3 = config1.with_fallback(config2)

        assert config3['a'] == {
            'b': 1,
            'c': 2,
            'd': 3
        }

        config4 = ConfigFactory.parse_string(
            """
            name: foo
            """
        )

        config5 = ConfigFactory.parse_string(
            u"""
            longName: "long "${?name}
            """,
            resolve=False
        )

        config6 = config4.with_fallback(config5)
        assert config6 == {
            'longName': 'long foo',
            'name': 'foo'
        }

    def test_fallback_substitutions_overwrite_file(self):
        config1 = ConfigFactory.parse_string(
            """
            {
                data-center-generic = { cluster-size: 8 }
                misc = "mist"
            }
            """
        )

        # use unicode path here for regression testing https://github.com/chimpler/pyhocon/issues/44
        config2 = config1.with_fallback(u'samples/aws.conf')
        assert config2 == {
            'data-center-generic': {'cluster-size': 8},
            'data-center-east': {'cluster-size': 8, 'name': 'east'},
            'misc': 'mist',
            'default-jvm-opts': ['-XX:+UseParNewGC'],
            'large-jvm-opts': ['-XX:+UseParNewGC', '-Xm16g']
        }

    def test_fallback_self_ref_substitutions_append(self):
        config1 = ConfigFactory.parse_string(
            """
            list = [ 1, 2, 3 ]
            """
        )
        config2 = ConfigFactory.parse_string(
            """
            list = ${list} [ 4, 5, 6 ]
            """,
            resolve=False
        )
        config2 = config2.with_fallback(config1)
        assert config2.get("list") == [1, 2, 3, 4, 5, 6]

    def test_fallback_self_ref_substitutions_append_plus_equals(self):
        config1 = ConfigFactory.parse_string(
            """
            list = [ 1, 2, 3 ]
            """
        )
        config2 = ConfigFactory.parse_string(
            """
            list += [ 4, 5, 6 ]
            """,
            resolve=False
        )
        config2 = config2.with_fallback(config1)
        assert config2.get("list") == [1, 2, 3, 4, 5, 6]

    def test_self_merge_ref_substitutions_object(self):
        config1 = ConfigFactory.parse_string(
            """
            a : { }
            b : 1
            c : ${a} { d : [ ${b} ] }
            """,
            resolve=False
        )
        config2 = ConfigFactory.parse_string(
            """
            e : ${a} {
            }
            """,
            resolve=False
        )
        merged = ConfigTree.merge_configs(config1, config2)
        ConfigParser.resolve_substitutions(merged)
        assert merged.get("c.d") == [1]

    def test_self_merge_ref_substitutions_object2(self):
        config1 = ConfigFactory.parse_string(
            """
            x : { v1: 1 }
            b1 : {v2: 2 }
            b = [${b1}]
            """,
            resolve=False
        )
        config2 = ConfigFactory.parse_string(
            """
            b2 : ${x} {v2: 3}
            b += [${b2}]
            """,
            resolve=False
        )
        merged = ConfigTree.merge_configs(config1, config2)
        ConfigParser.resolve_substitutions(merged)
        b = merged.get("b")
        assert len(b) == 2
        assert b[0] == {'v2': 2}
        assert b[1] == {'v1': 1, 'v2': 3}

    def test_self_merge_ref_substitutions_object3(self):
        config1 = ConfigFactory.parse_string(
            """
            b1 : { v1: 1 }
            b = [${b1}]
            """,
            resolve=False
        )
        config2 = ConfigFactory.parse_string(
            """
            b1 : { v1: 2, v2: 3 }
            """,
            resolve=False
        )
        merged = ConfigTree.merge_configs(config1, config2)
        ConfigParser.resolve_substitutions(merged)
        assert merged.get("b1") == {"v1": 2, "v2": 3}
        b = merged.get("b")
        assert len(b) == 1
        assert b[0] == {"v1": 2, "v2": 3}

    def test_fallback_self_ref_substitutions_merge(self):
        config1 = ConfigFactory.parse_string(
            """
            dict = { x: 1 }
            """
        )
        config2 = ConfigFactory.parse_string(
            """
            dict = ${dict} { y: 2 }
            """,
            resolve=False
        )
        config2 = config2.with_fallback(config1)
        assert config2.get("dict") == {'x': 1, 'y': 2}

    def test_fallback_self_ref_substitutions_concat_string(self):
        config1 = ConfigFactory.parse_string(
            """
            string = abc
            """
        )
        config2 = ConfigFactory.parse_string(
            """
            string = ${string}def
            """,
            resolve=False
        )
        result = config2.with_fallback(config1)
        assert result.get("string") == 'abcdef'

        # test no mutation on config1
        assert result is not config1
        # test no mutation on config2
        assert "abc" not in str(config2)

    def test_fallback_non_root(self):
        root = ConfigFactory.parse_string(
            """
            a = 1
            mid.b = 1
            """
        )

        config = root.get_config("mid").with_fallback(root)
        assert config['a'] == 1 and config['b'] == 1

    def test_object_field_substitution(self):
        config = ConfigFactory.parse_string(
            """
            A = ${Test}

            Test {
                field1 = 1
                field2 = ${Test.field1}"2"
                field3 = ${Test.field2}"3"
            }
            """
        )

        assert config.get_string("A.field1") == "1"
        assert config.get_string("A.field2") == "12"
        assert config.get_string("A.field3") == "123"
        assert config.get_string("Test.field1") == "1"
        assert config.get_string("Test.field2") == "12"
        assert config.get_string("Test.field3") == "123"

    def test_one_line_quote_escape(self):
        config = ConfigFactory.parse_string(
            """
            test_no_quotes: abc\\n\\n
            test_quotes: "abc\\n\\n"
            """
        )

        assert config == {
            'test_no_quotes': 'abc\n\n',
            'test_quotes': 'abc\n\n'
        }

    def test_multi_line_escape(self):
        config = ConfigFactory.parse_string(
            """
with-escaped-backslash: \"\"\"
\\\\
\"\"\"

with-newline-escape-sequence: \"\"\"
\\n
\"\"\"

with-escaped-newline-escape-sequence: \"\"\"
\\\\n
\"\"\"
            """
        )

        assert config['with-escaped-backslash'] == '\n\\\\\n'
        assert config['with-newline-escape-sequence'] == '\n\\n\n'
        assert config['with-escaped-newline-escape-sequence'] == '\n\\\\n\n'

    def test_multiline_with_backslash(self):
        config = ConfigFactory.parse_string(
            """
            test = line1 \
line2
test2 = test
            """)

        assert config == {
            'test': 'line1 line2',
            'test2': 'test'
        }

    def test_from_dict_with_dict(self):
        d = {
            'banana': 3,
            'apple': 4,
            'pear': 1,
            'orange': 2,
        }
        config = ConfigFactory.from_dict(d)
        assert config == d

    def test_from_dict_with_ordered_dict(self):
        d = OrderedDict()
        d['banana'] = 3
        d['apple'] = 4
        d['pear'] = 1
        d['orange'] = 2
        config = ConfigFactory.from_dict(d)
        assert config == d

    def test_from_dict_with_nested_dict(self):
        d = OrderedDict()
        d['banana'] = 3
        d['apple'] = 4
        d['pear'] = 1
        d['tree'] = {
            'a': 'abc\ntest\n',
            'b': [1, 2, 3]
        }
        config = ConfigFactory.from_dict(d)
        assert config == d

    def test_object_concat(self):
        config = ConfigFactory.parse_string(
            """o1 = {
                foo : {
                    a : 1
                    b : 2
                }
            }
            o2 = {
                foo : {
                    b : 3
                    c : 4
                }
            }
            o3 = ${o1} ${o2}
            """
        )

        assert config.get_int('o1.foo.b') == 2
        assert config.get_int('o2.foo.b') == 3
        assert config.get_int('o3.foo.b') == 3
        assert config.get_int('o1.foo.c', default=42) == 42
        assert config.get_int('o3.foo.a') == 1
        assert config.get_int('o3.foo.c') == 4

    def test_issue_75(self):
        config = ConfigFactory.parse_string(
            """base : {
              bar: ["a"]
            }

            sub : ${base} {
              baz: ${base.bar} ["b"]
            }

            sub2: ${sub}
            """
        )

        assert config.get_list('base.bar') == ["a"]
        assert config.get_list('sub.baz') == ["a", "b"]
        assert config.get_list('sub2.baz') == ["a", "b"]

    def test_plain_ordered_dict(self):
        config = ConfigFactory.parse_string(
            """
            e : ${a} {
            }
            """,
            resolve=False
        )
        with pytest.raises(ConfigException):
            config.as_plain_ordered_dict()

    def test_quoted_strings_with_ws(self):
        config = ConfigFactory.parse_string(
            """
            no_trailing_ws = "foo"  "bar  "
            trailing_ws = "foo"  "bar  "{ws}
            trailing_ws_with_comment = "foo"  "bar  "{ws}// comment
            """.format(ws='   '))

        assert config == {
            'no_trailing_ws': "foo  bar  ",
            'trailing_ws': "foo  bar  ",
            'trailing_ws_with_comment': "foo  bar  "
        }

    def test_unquoted_strings_with_ws(self):
        config = ConfigFactory.parse_string(
            """
            a = foo  bar
            """)

        assert config == {
            'a': 'foo  bar'
        }

    def test_quoted_unquoted_strings_with_ws(self):
        config = ConfigFactory.parse_string(
            """
            a = foo  "bar"   dummy
            """)

        assert config == {
            'a': 'foo  bar   dummy'
        }

    def test_quoted_unquoted_strings_with_ws_substitutions(self):
        config = ConfigFactory.parse_string(
            """
            x = 5
            b = test
            a = foo  "bar"  ${b} dummy
            c = foo          ${x}        bv
            d = foo          ${x}        43
            """)

        assert config == {
            'x': 5,
            'b': 'test',
            'a': 'foo  bar  test dummy',
            'c': 'foo          5        bv',
            'd': 'foo          5        43'
        }

    def test_complex_substitutions(self):
        config = ConfigFactory.parse_string(
            """
            a: 1
            b: ${c} {
              pa: [${a}]
              pb: ${b.pa}
            }
            c: { }
            d: { pc: ${b.pa} }
            e: ${b}
            """, resolve=True)

        assert config == {
            'a': 1,
            'b': {'pa': [1], 'pb': [1]},
            'c': {},
            'd': {'pc': [1]},
            'e': {'pa': [1], 'pb': [1]}
        }

    def test_assign_next_line(self):
        config = ConfigFactory.parse_string(
            """
            a = // abc
            abc

            c =
            5
            """)

        assert config == {
            'a': 'abc',
            'c': 5
        }

    @mock.patch.dict(os.environ, STRING_VAR='value_from_environment')
    def test_string_from_environment(self):
        config = ConfigFactory.parse_string(
            """
            string_from_env = ${STRING_VAR}
            """)
        assert config == {
            'string_from_env': 'value_from_environment'
        }

    @mock.patch.dict(os.environ, STRING_VAR='value_from_environment')
    def test_string_from_environment_self_ref(self):
        config = ConfigFactory.parse_string(
            """
            STRING_VAR = ${STRING_VAR}
            """)
        assert config == {
            'STRING_VAR': 'value_from_environment'
        }

    @mock.patch.dict(os.environ, STRING_VAR='value_from_environment')
    def test_string_from_environment_self_ref_optional(self):
        config = ConfigFactory.parse_string(
            """
            STRING_VAR = ${?STRING_VAR}
            """)
        assert config == {
            'STRING_VAR': 'value_from_environment'
        }

    @mock.patch.dict(os.environ, TRUE_OR_FALSE='false')
    def test_bool_from_environment(self):
        config = ConfigFactory.parse_string(
            """
            bool_from_env = ${TRUE_OR_FALSE}
            """)
        assert config == {
            'bool_from_env': 'false'
        }
        assert config.get_bool('bool_from_env') is False

    @mock.patch.dict(os.environ, INT_VAR='5')
    def test_int_from_environment(self):
        config = ConfigFactory.parse_string(
            """
            int_from_env = ${INT_VAR}
            """)
        assert config == {
            'int_from_env': '5'
        }
        assert config.get_int('int_from_env') == 5

    def test_unicode_dict_key(self):
        input_string = u"""
www.sample.com {
    us {
        name = "first domain"
    }
}
www.example-ö.com {
    us {
        name = "second domain"
    }
}
        """

        config = ConfigFactory.parse_string(input_string)

        assert config.get_string(u'www.sample.com.us.name') == 'first domain'
        assert config.get_string(u'www.example-ö.com.us.name') == 'second domain'
        with pytest.raises(ConfigWrongTypeException):
            config.put(u'www.example-ö', 'append_failure', append=True)
        with pytest.raises(ConfigMissingException):
            config.get_string(u'missing_unicode_key_ö')
        with pytest.raises(ConfigException):
            config.get_bool(u'www.example-ö.com.us.name')
        with pytest.raises(ConfigException):
            config.get_list(u'www.example-ö.com.us.name')
        with pytest.raises(ConfigException):
            config.get_config(u'www.example-ö.com.us.name')
        with pytest.raises(ConfigWrongTypeException):
            config.get_string(u'www.example-ö.com.us.name.missing')

    def test_with_comment_on_last_line(self):
        # Adress issue #102
        config_tree = ConfigFactory.parse_string("""
        foo: "1"
        bar: "2"
        # DO NOT CHANGE ANY OF THE ABOVE SETTINGS!""")
        assert config_tree == {
            'foo': '1',
            'bar': '2'
        }

    def test_triple_quotes_same_line(self):
        config_tree = ConfigFactory.parse_string('a:["""foo"""", "bar"]')
        assert config_tree == {
            'a': ['foo"', "bar"]
        }

    def test_pop(self):
        config_tree = ConfigFactory.parse_string('a:{b: 3, d: 6}')
        assert 3 == config_tree.pop('a.b', 5)
        assert 5 == config_tree.pop('a.c', 5)
        expected = {
            'a': {'d': 6}
        }
        assert expected == config_tree

    def test_merge_overriden(self):
        # Adress issue #110
        # ConfigValues must merge with its .overriden_value
        # if both are ConfigTree
        config_tree = ConfigFactory.parse_string("""
        foo: ${bar}
        foo: ${baz}
        bar:  {r: 1, s: 2}
        baz:  {s: 3, t: 4}
        """)
        assert 'r' in config_tree['foo'] and 't' in config_tree['foo'] and config_tree['foo']['s'] == 3

    def test_attr_syntax(self):
        config = ConfigFactory.parse_string(
            """
            a: 1
            b: {
              pb: 5
            }
            """)
        assert 5 == config.b.pb

    def test_escape_quote(self):
        config = ConfigFactory.parse_string(
            """
            quoted: "abc\\"test"
            unquoted: abc\\"test
            """)
        assert 'abc"test' == config['quoted']
        assert 'abc"test' == config['unquoted']

    def test_escape_quote_complex(self):
        config = ConfigFactory.parse_string(
            """
            value: "{\\"critical\\":\\"0.00\\",\\"warning\\":\\"99.99\\"}"
            """
        )

        assert '{"critical":"0.00","warning":"99.99"}' == config['value']

    def test_keys_with_slash(self):
        config = ConfigFactory.parse_string(
            """
            /abc/cde1: abc
            "/abc/cde2": "cde"
            /abc/cde3: "fgh"
            """)
        assert 'abc' == config['/abc/cde1']
        assert 'cde' == config['/abc/cde2']
        assert 'fgh' == config['/abc/cde3']

    def test_mutation_values(self):
        config = ConfigFactory.parse_string(
            """
            common : {
            }

            b1 = []

            var = "wrong"

            compilerCommon : ${common} {
                VAR : ${var}
            }

            substrate-suite: {
                VAR  : "right"
            }
            b1 = [
              ${compilerCommon} ${substrate-suite}
              ${compilerCommon} ${substrate-suite}
            ]

            b2 = [
              ${compilerCommon} ${substrate-suite}
              ${compilerCommon} ${substrate-suite}
            ]
            """)

        assert config.get("b1")[1]['VAR'] == 'right'
        assert config.get("b2")[1]['VAR'] == 'right'

    def test_escape_sequences_json_equivalence(self):
        """
        Quoted strings are in the same format as JSON strings,
        See: https://github.com/lightbend/config/blob/master/HOCON.md#unchanged-from-json
        """
        source = r"""
        {
            "plain-backslash": "\\",
            "tab": "\t",
            "no-tab": "\\t",
            "newline": "\n",
            "no-newline": "\\n",
            "cr": "\r",
            "no-cr": "\\r",
            "windows": "c:\\temp"
        }
        """
        expected = {
            'plain-backslash': '\\',
            'tab': '\t',
            'no-tab': '\\t',
            'newline': '\n',
            'no-newline': '\\n',
            'cr': '\r',
            'no-cr': '\\r',
            'windows': 'c:\\temp',
        }
        config = ConfigFactory.parse_string(source)
        assert config == expected
        assert config == json.loads(source)


try:
    from dateutil.relativedelta import relativedelta

    @pytest.mark.parametrize('data_set', [
        ('a: 1 months', relativedelta(months=1)),
        ('a: 1months', relativedelta(months=1)),
        ('a: 2 month', relativedelta(months=2)),
        ('a: 3 mo', relativedelta(months=3)),
        ('a: 3mo', relativedelta(months=3)),
        ('a: 3 mon', '3 mon'),

        ('a: 1 years', relativedelta(years=1)),
        ('a: 1years', relativedelta(years=1)),
        ('a: 2 year', relativedelta(years=2)),
        ('a: 3 y', relativedelta(years=3)),
        ('a: 3y', relativedelta(years=3)),

    ])
    def test_parse_string_with_duration_optional_units(data_set):
        config = ConfigFactory.parse_string(data_set[0])

        assert config['a'] == data_set[1]
except Exception:
    pass
