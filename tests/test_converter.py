# -*- encoding: utf-8 -*-

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
