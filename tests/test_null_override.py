import copy

import pytest

from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigTree


@pytest.mark.parametrize('replacement, expected', [('{}', {}), ('{d: 2}', {'d': 2})])
@pytest.mark.parametrize('template', [
    'a { b { c: 1 } }\na { b: null, b: REPLACEMENT }',
    'a = { b { c: 1 } } { b: null, b: REPLACEMENT }',
    'outer { a { b { c: 1 } } }\nouter { a { b: null, b: REPLACEMENT } }',
])
def test_null_prevents_merging_earlier_object(template, replacement, expected):
    config = ConfigFactory.parse_string(template.replace('REPLACEMENT', replacement))
    path = 'outer.a.b' if template.startswith('outer') else 'a.b'
    assert config[path] == expected


def test_null_before_dotted_assignment_prevents_merging():
    config = ConfigFactory.parse_string('a { b { c: 1 } }\na { b: null, b.d: 2 }')
    assert config['a.b'] == {'d': 2}


def test_objects_after_null_still_merge_with_each_other():
    config = ConfigFactory.parse_string('''
        a { b { c: 1 }, sibling: 9 }
        a { b: null, b { d: 2 }, b { e: 3 } }
        a { b { f: 4 } }
    ''')
    assert config['a'] == {'b': {'d': 2, 'e': 3, 'f': 4}, 'sibling': 9}


@pytest.mark.parametrize('copy_tree', [lambda value: value, copy.copy, copy.deepcopy, lambda value: value.copy()])
def test_null_override_survives_config_copies_and_fallback(copy_tree):
    fallback = ConfigFactory.parse_string('a { b { c: 1 }, sibling: 9 }')
    config = copy_tree(ConfigFactory.parse_string('a { b: null, b { d: 2 } }'))
    result = config.with_fallback(fallback)
    assert result['a'] == {'b': {'d': 2}, 'sibling': 9}
    assert fallback['a.b'] == {'c': 1}
    assert config['a.b'] == {'d': 2}


@pytest.mark.parametrize('copy_trees', [False, True])
def test_merge_retains_reset_when_used_in_another_merge(copy_trees):
    first = ConfigFactory.parse_string('a { b: null, b { d: 2 } }')
    second = ConfigFactory.parse_string('a { b { e: 3 } }')
    combined = ConfigTree.merge_configs(first, second, copy_trees=copy_trees)
    fallback = ConfigFactory.parse_string('a { b { c: 1 } }')
    assert combined.with_fallback(fallback)['a.b'] == {'d': 2, 'e': 3}


def test_object_merging_without_null_keeps_earlier_values():
    config = ConfigFactory.parse_string('a { b { c: 1 } }\na { b {}, b { d: 2 } }')
    assert config['a.b'] == {'c': 1, 'd': 2}


def test_final_null_still_replaces_the_object():
    config = ConfigFactory.parse_string('a { b { c: 1 } }\na { b: null }')
    assert config['a.b'] is None


@pytest.mark.parametrize('remove', [
    lambda config: config.__delitem__('b'),
    lambda config: config.pop('b'),
    lambda config: config.popitem(),
    lambda config: config.clear(),
])
@pytest.mark.parametrize('copy_tree', [copy.copy, copy.deepcopy, lambda value: value.copy()])
def test_deleted_override_does_not_affect_reused_key_or_original_copy(remove, copy_tree):
    original = ConfigFactory.parse_string('b: null\nb { d: 2 }')
    config = copy_tree(original)
    remove(config)
    config.put('b.e', 3)
    fallback = ConfigFactory.parse_string('b { c: 1 }')
    assert config.with_fallback(fallback)['b'] == {'c': 1, 'e': 3}
    assert original.with_fallback(fallback)['b'] == {'d': 2}


@pytest.mark.parametrize('replacement, expected', [
    ('${v}', {'d': 2}),
    ('${v} {e: 3}', {'d': 2, 'e': 3}),
    ('{d: 2}, b: ${?MISSING_PYHOCON_268}', {'d': 2}),
])
def test_substitution_after_null_does_not_restore_earlier_object(replacement, expected, monkeypatch):
    monkeypatch.delenv('MISSING_PYHOCON_268', raising=False)
    config = ConfigFactory.parse_string('a { b { c: 1 } }\na { b: null, b: ' + replacement + ' }\nv { d: 2 }')
    assert config['a.b'] == expected
