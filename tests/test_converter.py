# -*- encoding: utf-8 -*-
from datetime import timedelta

from pyhocon import ConfigTree
from pyhocon.converter import HOCONConverter


def to_json(obj):
    return HOCONConverter.to_json(ConfigTree(obj), compact=True, indent=1)


class TestConverterToJson(object):
    def test_escape_control_characters(self):
        assert '{\n "a": "\\u0000"\n}' == to_json({'a': '\x00'})
        assert '{\n "a": "\\u0001"\n}' == to_json({'a': '\x01'})
        assert '{\n "a": "\\u0002"\n}' == to_json({'a': '\x02'})
        assert '{\n "a": "\\u0003"\n}' == to_json({'a': '\x03'})
        assert '{\n "a": "\\u0004"\n}' == to_json({'a': '\x04'})
        assert '{\n "a": "\\u0005"\n}' == to_json({'a': '\x05'})
        assert '{\n "a": "\\u0006"\n}' == to_json({'a': '\x06'})
        assert '{\n "a": "\\u0007"\n}' == to_json({'a': '\x07'})
        assert '{\n "a": "\\b"\n}' == to_json({'a': '\x08'})
        assert '{\n "a": "\\t"\n}' == to_json({'a': '\x09'})
        assert '{\n "a": "\\n"\n}' == to_json({'a': '\x0a'})
        assert '{\n "a": "\\u000b"\n}' == to_json({'a': '\x0b'})
        assert '{\n "a": "\\f"\n}' == to_json({'a': '\x0c'})
        assert '{\n "a": "\\r"\n}' == to_json({'a': '\x0d'})
        assert '{\n "a": "\\u000e"\n}' == to_json({'a': '\x0e'})
        assert '{\n "a": "\\u000f"\n}' == to_json({'a': '\x0f'})
        assert '{\n "a": "\\u0010"\n}' == to_json({'a': '\x10'})
        assert '{\n "a": "\\u0011"\n}' == to_json({'a': '\x11'})
        assert '{\n "a": "\\u0012"\n}' == to_json({'a': '\x12'})
        assert '{\n "a": "\\u0013"\n}' == to_json({'a': '\x13'})
        assert '{\n "a": "\\u0014"\n}' == to_json({'a': '\x14'})
        assert '{\n "a": "\\u0015"\n}' == to_json({'a': '\x15'})
        assert '{\n "a": "\\u0016"\n}' == to_json({'a': '\x16'})
        assert '{\n "a": "\\u0017"\n}' == to_json({'a': '\x17'})
        assert '{\n "a": "\\u0018"\n}' == to_json({'a': '\x18'})
        assert '{\n "a": "\\u0019"\n}' == to_json({'a': '\x19'})
        assert '{\n "a": "\\u001a"\n}' == to_json({'a': '\x1a'})
        assert '{\n "a": "\\u001b"\n}' == to_json({'a': '\x1b'})
        assert '{\n "a": "\\u001c"\n}' == to_json({'a': '\x1c'})
        assert '{\n "a": "\\u001d"\n}' == to_json({'a': '\x1d'})
        assert '{\n "a": "\\u001e"\n}' == to_json({'a': '\x1e'})
        assert '{\n "a": "\\u001f"\n}' == to_json({'a': '\x1f'})

    def test_escape_quote(self):
        assert '{\n "a": "\\""\n}' == to_json({'a': '"'})

    def test_escape_reverse_solidus(self):
        assert '{\n "a": "\\\\"\n}' == to_json({'a': '\\'})

    def test_format_multiline_string(self):
        assert '{\n "a": "b\\nc"\n}' == to_json({'a': 'b\nc'})
        assert '{\n "a": "\\nc"\n}' == to_json({'a': '\nc'})
        assert '{\n "a": "b\\n"\n}' == to_json({'a': 'b\n'})
        assert '{\n "a": "\\n\\n"\n}' == to_json({'a': '\n\n'})


def to_hocon(obj):
    return HOCONConverter.to_hocon(ConfigTree(obj))


class TestConverterToHocon(object):
    def test_escape_control_characters(self):
        assert r'a = "\u0000"' == to_hocon({'a': '\x00'})
        assert r'a = "\u0001"' == to_hocon({'a': '\x01'})
        assert r'a = "\u0002"' == to_hocon({'a': '\x02'})
        assert r'a = "\u0003"' == to_hocon({'a': '\x03'})
        assert r'a = "\u0004"' == to_hocon({'a': '\x04'})
        assert r'a = "\u0005"' == to_hocon({'a': '\x05'})
        assert r'a = "\u0006"' == to_hocon({'a': '\x06'})
        assert r'a = "\u0007"' == to_hocon({'a': '\x07'})
        assert r'a = "\b"' == to_hocon({'a': '\x08'})
        assert r'a = "\t"' == to_hocon({'a': '\x09'})
        assert r'a = "\n"' == to_hocon({'a': '\x0a'})
        assert r'a = "\u000b"' == to_hocon({'a': '\x0b'})
        assert r'a = "\f"' == to_hocon({'a': '\x0c'})
        assert r'a = "\r"' == to_hocon({'a': '\x0d'})
        assert r'a = "\u000e"' == to_hocon({'a': '\x0e'})
        assert r'a = "\u000f"' == to_hocon({'a': '\x0f'})
        assert r'a = "\u0010"' == to_hocon({'a': '\x10'})
        assert r'a = "\u0011"' == to_hocon({'a': '\x11'})
        assert r'a = "\u0012"' == to_hocon({'a': '\x12'})
        assert r'a = "\u0013"' == to_hocon({'a': '\x13'})
        assert r'a = "\u0014"' == to_hocon({'a': '\x14'})
        assert r'a = "\u0015"' == to_hocon({'a': '\x15'})
        assert r'a = "\u0016"' == to_hocon({'a': '\x16'})
        assert r'a = "\u0017"' == to_hocon({'a': '\x17'})
        assert r'a = "\u0018"' == to_hocon({'a': '\x18'})
        assert r'a = "\u0019"' == to_hocon({'a': '\x19'})
        assert r'a = "\u001a"' == to_hocon({'a': '\x1a'})
        assert r'a = "\u001b"' == to_hocon({'a': '\x1b'})
        assert r'a = "\u001c"' == to_hocon({'a': '\x1c'})
        assert r'a = "\u001d"' == to_hocon({'a': '\x1d'})
        assert r'a = "\u001e"' == to_hocon({'a': '\x1e'})
        assert r'a = "\u001f"' == to_hocon({'a': '\x1f'})

    def test_escape_quote(self):
        assert r'a = "\""' == to_hocon({'a': '"'})

    def test_escape_reverse_solidus(self):
        assert r'a = "\\"' == to_hocon({'a': '\\'})

    def test_format_multiline_string(self):
        assert 'a = """b\nc"""' == to_hocon({'a': 'b\nc'})
        assert 'a = """\nc"""' == to_hocon({'a': '\nc'})
        assert 'a = """b\n"""' == to_hocon({'a': 'b\n'})
        assert 'a = """\n\n"""' == to_hocon({'a': '\n\n'})

    def test_format_time_delta(self):
        for time_delta, expected_result in ((timedelta(days=0), 'td = 0 seconds'),
                                            (timedelta(days=5), 'td = 5 days'),
                                            (timedelta(seconds=51), 'td = 51 seconds'),
                                            (timedelta(microseconds=786), 'td = 786 microseconds')):
            assert expected_result == to_hocon({'td': time_delta})

    def test_format_relativedelta(self):
        try:
            from dateutil.relativedelta import relativedelta
        except Exception:
            return

        for time_delta, expected_result in ((relativedelta(seconds=0), 'td = 0 seconds'),
                                            (relativedelta(hours=0), 'td = 0 seconds'),
                                            (relativedelta(days=5), 'td = 5 days'),
                                            (relativedelta(weeks=3), 'td = 21 days'),
                                            (relativedelta(hours=2), 'td = 2 hours'),
                                            (relativedelta(minutes=43), 'td = 43 minutes'),):
            assert expected_result == to_hocon({'td': time_delta})


class TestConverterToYamlKeys(object):
    @staticmethod
    def config_with_literal_keys(values):
        # Match ConfigTree's representation of literal path/syntax characters.
        return ConfigTree((('"' + key + '"') if any(char in '$}[]:=+#`^?!@*&.' for char in key) else key, value)
                          for key, value in values.items())

    def test_implicit_scalar_keys_remain_strings(self):
        import yaml

        keys = ['true', 'True', 'TRUE', 'false', 'False', 'FALSE',
                'null', 'Null', 'NULL', '~', 'y', 'Y', 'n', 'N',
                'yes', 'Yes', 'YES', 'no', 'No', 'NO',
                'on', 'On', 'ON', 'off', 'Off', 'OFF',
                '1', '123', '0', '-1', '+1', '01', '0o12', '0x10', '0b10',
                '1.0', '1e3', '1E+3', '.inf', '-.Inf', '.nan', '1:20', '2026-10-19']
        expected = dict((key, 'value-' + str(index)) for index, key in enumerate(keys))
        actual = yaml.safe_load(HOCONConverter.to_yaml(self.config_with_literal_keys(expected)))
        assert actual == expected
        assert all(isinstance(key, str) for key in actual)
        assert len(actual) == len(expected)
        # Explicit string scalars also avoid YAML 1.2 resolver differences.
        for node, _ in yaml.compose(HOCONConverter.to_yaml(self.config_with_literal_keys(expected))).value:
            assert node.style == '"'
            assert node.tag == 'tag:yaml.org,2002:str'

    def test_yaml_syntax_keys_remain_strings(self):
        import yaml

        keys = [':', 'a: b', '#comment', 'a # b', '[item]', '{item}',
                '*alias', '&anchor', '!tag', '? key', '- key', '|', '>', '%directive',
                '---', '...', ' leading', 'trailing ', 'a"b', 'a\\b',
                'a\nb', 'a\rb', 'a\tb', 'a\x00b', 'a\x7fb', 'a\x85b', 'a\x9fb',
                'a\u2028b', 'a\u2029b', 'café', '😀']
        expected = dict((key, 'value-' + str(index)) for index, key in enumerate(keys))
        actual = yaml.safe_load(HOCONConverter.to_yaml(self.config_with_literal_keys(expected)))
        assert actual == expected
        assert all(isinstance(key, str) for key in actual)

    def test_ordinary_key_output_is_unchanged(self):
        config = ConfigTree([('alpha', 'first'), ('server_name', 'second'),
                             ('key123', 'third'), ('trueish', 'fourth'), ('a-b', 'fifth')])
        assert HOCONConverter.to_yaml(config) == (
            'alpha: first\nserver_name: second\nkey123: third\ntrueish: fourth\na-b: fifth')

    def test_quoted_dotted_key_output_is_unchanged(self):
        assert HOCONConverter.to_yaml(ConfigTree({'"a.b"': 'value'})) == 'a.b: value'

    def test_keys_in_nested_objects_and_lists(self):
        import yaml

        config = ConfigTree({'outer': ConfigTree({'true': 'first', '1': 'second'}),
                             'items': [ConfigTree({'null': 'third', '123': 'fourth'})]})
        assert yaml.safe_load(HOCONConverter.to_yaml(config)) == {
            'outer': {'true': 'first', '1': 'second'},
            'items': [{'null': 'third', '123': 'fourth'}]}

    def test_long_key_boundaries(self):
        import yaml

        for key, explicit in [('é' * 1022, False), ('é' * 1023, True),
                              ('a ' * 511 + 'b', True), ('a' * 1024, False), ('a' * 1025, True),
                              ('a\nb' * 256, True)]:
            config = self.config_with_literal_keys({key: 'value'})
            output = HOCONConverter.to_yaml(config)
            assert output.startswith('? ') == explicit
            assert yaml.safe_load(output) == {key: 'value'}

    def test_long_keys_nested_with_custom_indent(self):
        import yaml

        key = 'é' * 1023
        inner = self.config_with_literal_keys({key: ConfigTree({'child': 'value'})})
        config = ConfigTree({'outer': inner, 'items': [inner]})
        expected = {'outer': {key: {'child': 'value'}}, 'items': [{key: {'child': 'value'}}]}
        for indent in (2, 4):
            output = HOCONConverter.to_yaml(config, indent=indent)
            assert '\n' + ' ' * indent + '? ' in output
            assert '\n' + ' ' * indent + ': ' in output
            assert yaml.safe_load(output) == expected

    def test_long_previously_readable_keys(self):
        import yaml

        for key in ['é' * 1023, 'a ' * 511 + 'b']:
            output = HOCONConverter.to_yaml(ConfigTree({key: 'value'}))
            assert yaml.safe_load(output) == {key: 'value'}
