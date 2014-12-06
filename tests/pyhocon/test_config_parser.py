from pyhocon import ConfigFactory


class TestConfigParser(object):

    def test_parse_simple_value(self):
        config = ConfigFactory.parseString(
            """t = {
                c = 5
                d = true
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
