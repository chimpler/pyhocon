from pyhocon import ConfigFactory


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
        assert map(lambda l: l.strip(), config.get('t.e.y.i').split('\n')) == ['', '"first line"', '"second" line', '']
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

    def test_substitutions(self):
        config = ConfigFactory.parse_string(
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

        assert config.get('a.b.c') == 5
        assert config.get('d') == 'test 5 me'

    def test_cascade_substitutions(self):
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

    def test_include_dict(self):
        config = ConfigFactory.parse_file("samples/animals.conf")
        assert config.get('cat.garfield.say') == 'meow'
        assert config.get('dog.mutt.hates.garfield.say') == 'meow'
