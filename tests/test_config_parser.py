import tempfile
from pyparsing import ParseSyntaxException, ParseException
import pytest
from pyhocon import ConfigFactory, ConfigSubstitutionException
from pyhocon.exceptions import ConfigMissingException, ConfigWrongTypeException
try:  # pragma: no cover
    from collections import OrderedDict
except ImportError:  # pragma: no cover
    from ordereddict import OrderedDict


class TestConfigParser(object):
    def test_parse_simple_value(self):
        config = ConfigFactory.parse_string(
            """t = {
                c = 5
                "d" = true
                e.y = {
                    f: 7
                    g: "hey dude!"
                    h: hey man!
                    i = \"\"\"
                        "first line"
                        "second" line
                        \"\"\"
                }
                j = [1, 2, 3]
                u = 192.168.1.3/32
            }
            """
        )

        assert config.get_string('t.c') == '5'
        assert config.get_int('t.c') == 5
        assert config.get('t.e.y.f') == 7
        assert config.get('t.e.y.g') == 'hey dude!'
        assert config.get('t.e.y.h') == 'hey man!'
        assert [l.strip() for l in config.get('t.e.y.i').split('\n')] == ['', '"first line"', '"second" line', '']
        assert config.get_bool('t.d') is True
        assert config.get_int('t.e.y.f') == 7
        assert config.get('t.j') == [1, 2, 3]
        assert config.get('t.u') == '192.168.1.3/32'

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
            c=the man!,
            d=woof,
            a-b-c-d=test,
            a b c d=test2,
            "a b c d e"=test3
            """
        )
        assert config.get('a') == 1
        assert config.get('b') == 'abc'
        assert config.get('c') == 'the man!'
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
            """
        )
        assert config.get('a') is None

    def test_parse_empty(self):
        config = ConfigFactory.parse_string(
            """
            a =
            b =   // test
            c =   # test
            d =   ,
            e =  ,  // test
            f =    , # test
            """
        )
        assert config.get('a') == ''
        assert config.get('b') == ''
        assert config.get('c') == ''

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
            application.foo = 128m
            application.large-jvm-opts = [-XX:+UseParNewGC] [-Xm16g, ${application.foo}]
            application.large-jvm-opts2 = [-Xm16g, ${application.foo}] [-XX:+UseParNewGC]
            """)

        assert config["application.large-jvm-opts"] == [
            '-XX:+UseParNewGC',
            '-Xm16g',
            '128m'
        ]

        assert config["application.large-jvm-opts2"] == [
            '-Xm16g',
            '128m',
            '-XX:+UseParNewGC',
        ]

    def test_substitution_list_with_append_substitution(self):
        config = ConfigFactory.parse_string(
            """
            application.foo = 128m
            application.default-jvm-opts = [-XX:+UseParNewGC]
            application.large-jvm-opts = ${application.default-jvm-opts} [-Xm16g, ${application.foo}]
            application.large-jvm-opts2 = [-Xm16g, ${application.foo}] ${application.default-jvm-opts}
            """)

        assert config["application.large-jvm-opts"] == [
            '-XX:+UseParNewGC',
            '-Xm16g',
            '128m'
        ]

        assert config["application.large-jvm-opts2"] == [
            '-Xm16g',
            '128m',
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

    def test_include_dict_from_samples(self):
        config = ConfigFactory.parse_file("samples/animals.conf")
        assert config.get('cat.garfield.say') == 'meow'
        assert config.get('dog.mutt.hates.garfield.say') == 'meow'

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

    def test_include_list(self):
        with tempfile.NamedTemporaryFile('w') as fdin:
            fdin.write('[1, 2]')
            fdin.flush()

            config1 = ConfigFactory.parse_string(
                """
                a: [
                    include "{tmp_file}"
                    3
                    4
                ]
                """.format(tmp_file=fdin.name)
            )
            assert config1['a'] == [1, 2, 3, 4]

            config2 = ConfigFactory.parse_string(
                """
                a: [
                    3
                    4
                    include "{tmp_file}"
                ]
                """.format(tmp_file=fdin.name)
            )
            assert config2['a'] == [3, 4, 1, 2]

            config3 = ConfigFactory.parse_string(
                """
                a: [
                    3
                    include "{tmp_file}"
                    4
                ]
                """.format(tmp_file=fdin.name)
            )
            assert config3['a'] == [3, 1, 2, 4]

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

        assert config.get_string("Test.field3") == "123"

    def test_one_line_quote_escape(self):
        config = ConfigFactory.parse_string(
            """
            test: "abc\n\n"
            """
        )

        assert config['test'] == 'abc\n\n'

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
