import json

import pytest
from pyparsing import ParseBaseException

from pyhocon import ConfigFactory, ConfigTree
from pyhocon.exceptions import ConfigMissingException


@pytest.mark.parametrize('value', ['', 'value', 0, True, None, [], [1, 2], {}, {'child': 1}, {'': ''}])
def test_empty_json_key(value):
    source = json.dumps({'': value})
    config = ConfigFactory.parse_string(source)
    assert config.as_plain_ordered_dict() == json.loads(source)
    assert config[''] == config['""']
    assert '' in config


@pytest.mark.parametrize('source', ['{"": ""}', '"": ""', '"" = ""', '"""""" = ""'])
def test_empty_key_and_value(source):
    assert ConfigFactory.parse_string(source) == {'': ''}


@pytest.mark.parametrize('source, expected, path', [
    ('outer { "": 1 }', {'outer': {'': 1}}, 'outer.""'),
    ('"" { child: 1 }', {'': {'child': 1}}, '"".child'),
    ('"" { "": 1 }', {'': {'': 1}}, '"".""'),
    ('"" { "a.b": 1 }', {'': {'a.b': 1}}, '""."a.b"'),
    ('"a.b" { "": 1 }', {'a.b': {'': 1}}, '"a.b".""'),
])
def test_empty_nested_key(source, expected, path):
    config = ConfigFactory.parse_string(source)
    assert config.as_plain_ordered_dict() == expected
    assert config[path] == 1


def test_empty_key_in_list():
    config = ConfigFactory.parse_string('items = [{"": 1}, {"": 2}]')
    assert config['items'] == [{'': 1}, {'': 2}]


def test_empty_key_override():
    config = ConfigFactory.parse_string('"" = 1\n"" = 2')
    assert config == {'': 2}


def test_empty_key_object_merge():
    config = ConfigFactory.parse_string('"" { a = 1 }\n"" { b = 2 }')
    assert config == {'': {'a': 1, 'b': 2}}


def test_missing_empty_key():
    config = ConfigFactory.parse_string('{}')
    assert '' not in config
    assert config.get('', 'fallback') == 'fallback'
    with pytest.raises(ConfigMissingException):
        config.get('')


@pytest.mark.parametrize('key, expected', [
    ('', ['']),
    ('""', ['']),
    ('a', ['a']),
    ('"a"', ['a']),
    ('"""a"""', ['a']),
    ('a.b', ['a', 'b']),
    ('"a.b"', ['"a.b"']),
    ('a."b.c"', ['a', '"b.c"']),
    ('a.""', ['a', '']),
    ('"".a', ['', 'a']),
])
def test_empty_key_path_and_nonempty_controls(key, expected):
    assert ConfigTree.parse_key(key) == expected


def test_empty_key_preserves_literal_and_dotted_keys():
    config = ConfigFactory.parse_string('"" = 1\n"a.b" = 2\na.b = 3')
    assert config[''] == 1
    assert config['"a.b"'] == 2
    assert config['a.b'] == 3


@pytest.mark.parametrize('source', [': 1', '= 1'])
def test_unquoted_missing_key_is_invalid(source):
    with pytest.raises(ParseBaseException):
        ConfigFactory.parse_string(source)


@pytest.mark.parametrize('source', ['', '{}', ' # comment\n'])
def test_empty_document_is_unchanged(source):
    assert ConfigFactory.parse_string(source) == {}
