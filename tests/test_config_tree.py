import pytest
from collections import OrderedDict
from pyhocon.config_tree import ConfigTree, NoneValue
from pyhocon.exceptions import (
    ConfigMissingException, ConfigWrongTypeException, ConfigException)
from pyhocon.config_parser import ConfigFactory
from pyhocon.tool import HOCONConverter


class TestConfigTree(object):

    def test_config_tree_quoted_string(self):
        config_tree = ConfigTree()
        config_tree.put("a.b.c", "value")
        assert config_tree.get("a.b.c") == "value"

        with pytest.raises(ConfigMissingException):
            assert config_tree.get("a.b.d")

        with pytest.raises(ConfigMissingException):
            config_tree.get("a.d.e")

        with pytest.raises(ConfigWrongTypeException):
            config_tree.get("a.b.c.e")

    def test_config_list(self):
        config_tree = ConfigTree()

        config_tree.put("a.b.c", [4, 5])
        assert config_tree.get("a.b.c") == [4, 5]

        config_tree.put("a.b.c", [6, 7])
        assert config_tree.get("a.b.c") == [6, 7]

        config_tree.put("a.b.c", [8, 9], True)
        assert config_tree.get("a.b.c") == [6, 7, 8, 9]

    def test_numerically_index_objects_to_arrays(self):
        config_tree = ConfigTree()
        config_tree.put("list.2", "b")
        config_tree.put("list.0", "a")
        assert config_tree.get_list("list") == ["a", "b"]

        config_tree.put("invalid-list.a", "c")
        config_tree.put("invalid-list.b", "d")
        with pytest.raises(ConfigException):
            config_tree.get_list("invalid-list")

    def test_config_tree_number(self):
        config_tree = ConfigTree()
        config_tree.put("a.b.c", 5)
        config_tree.put("a.b.e", 4.5)
        assert config_tree.get("a.b.c") == 5
        assert config_tree.get("a.b.e") == 4.5

    def test_config_tree_iterator(self):
        config_tree = ConfigTree()
        config_tree.put("a.b.c", 5)
        for k in config_tree:
            assert k == "a"
            assert config_tree[k]["b.c"] == 5

    def test_config_logging(self):
        import logging.config
        config_tree = ConfigTree()
        config_tree.put('version', 1)
        config_tree.put('root.level', logging.INFO)
        assert dict(config_tree)['version'] == 1

    def test_config_tree_null(self):
        config_tree = ConfigTree()
        config_tree.put("a.b.c", None)
        assert config_tree.get("a.b.c") is None

    def test_config_tree_null_items(self):
        config_tree = ConfigTree()
        config_tree.put("a", NoneValue())
        assert list(config_tree.items()) == [("a", None)]

    def test_getters(self):
        config_tree = ConfigTree()
        config_tree.put("int", 5)
        assert config_tree["int"] == 5
        assert config_tree.get("int") == 5
        assert config_tree.get_int("int") == 5

        config_tree.put("float", 4.5)
        assert config_tree["float"] == 4.5
        assert config_tree.get("float") == 4.5
        assert config_tree.get_float("float") == 4.5

        config_tree.put("string", "string")
        assert config_tree["string"] == "string"
        assert config_tree.get("string") == "string"
        assert config_tree.get_string("string") == "string"

        config_tree.put("list", [1, 2, 3])
        assert config_tree["list"] == [1, 2, 3]
        assert config_tree.get("list") == [1, 2, 3]
        assert config_tree.get_list("list") == [1, 2, 3]

        config_tree.put("bool", True)
        assert config_tree["bool"] is True
        assert config_tree.get("bool") is True
        assert config_tree.get_bool("bool") is True

        config_tree.put("config", {'a': 5})
        assert config_tree["config"] == {'a': 5}
        assert config_tree.get("config") == {'a': 5}
        assert config_tree.get_config("config") == {'a': 5}

    def test_getters_with_default(self):
        config_tree = ConfigTree()
        config_tree.put("int", 5)
        assert config_tree.get("int-new", 1) == 1
        assert config_tree.get_int("int", 1) == 5
        assert config_tree.get_int("int-new", 1) == 1
        assert config_tree.get_int("int-new.test", 1) == 1

        config_tree.put("float", 4.5)
        assert config_tree.get("float", 1.0) == 4.5
        assert config_tree.get("float-new", 1.0) == 1.0
        assert config_tree.get_float("float", 1.0) == 4.5
        assert config_tree.get_float("float-new", 1.0) == 1.0
        assert config_tree.get_float("float-new.test", 1.0) == 1.0

        config_tree.put("string", "string")
        assert config_tree.get("string", "default") == "string"
        assert config_tree.get("string-new", "default") == "default"
        assert config_tree.get_string("string", "default") == "string"
        assert config_tree.get_string("string-new", "default") == "default"
        assert config_tree.get_string("string-new.test", "default") == "default"

        config_tree.put("list", [1, 2, 3])
        assert config_tree.get("list", [4]) == [1, 2, 3]
        assert config_tree.get("list-new", [4]) == [4]
        assert config_tree.get_list("list", [4]) == [1, 2, 3]
        assert config_tree.get_list("list-new", [4]) == [4]

        config_tree.put("bool", True)
        assert config_tree.get("bool", False) is True
        assert config_tree.get("bool-new", False) is False
        assert config_tree.get_bool("bool", False) is True
        assert config_tree.get_bool("bool-new", False) is False

        config_tree.put("config", {'a': 5})
        assert config_tree.get("config", {'b': 1}) == {'a': 5}
        assert config_tree.get("config-new", {'b': 1}) == {'b': 1}
        assert config_tree.get_config("config", {'b': 1}) == {'a': 5}
        assert config_tree.get_config("config-new", {'b': 1}) == {'b': 1}

    def test_getter_type_conversion_string_to_bool(self):
        config_tree = ConfigTree()
        config_tree.put("bool-string-true", "true")
        assert config_tree.get_bool("bool-string-true") is True

        config_tree.put("bool-string-true", "True")
        assert config_tree.get_bool("bool-string-true") is True

        config_tree.put("bool-string-false", "false")
        assert config_tree.get_bool("bool-string-false") is False

        config_tree.put("bool-string-false", "False")
        assert config_tree.get_bool("bool-string-false") is False

        config_tree.put("bool-string-yes", "yes")
        assert config_tree.get_bool("bool-string-yes") is True

        config_tree.put("bool-string-no", "no")
        assert config_tree.get_bool("bool-string-no") is False

        config_tree.put("bool-string-on", "on")
        assert config_tree.get_bool("bool-string-on") is True

        config_tree.put("bool-string-off", "off")
        assert config_tree.get_bool("bool-string-off") is False

        config_tree.put("invalid-bool-string", "invalid")
        with pytest.raises(ConfigException):
            config_tree.get_bool("invalid-bool-string")

    def test_getter_type_conversion_bool_to_string(self):
        config_tree = ConfigTree()
        config_tree.put("bool-true", True)
        assert config_tree.get_string("bool-true") == "true"

        config_tree.put("bool-false", False)
        assert config_tree.get_string("bool-false") == "false"

    def test_getter_type_conversion_number_to_string(self):
        config_tree = ConfigTree()
        config_tree.put("int", 5)
        assert config_tree.get_string("int") == "5"

        config_tree.put("float", 2.345)
        assert config_tree.get_string("float") == "2.345"

    def test_overrides_int_with_config_no_append(self):
        config_tree = ConfigTree()
        config_tree.put("int", 5)
        config_tree.put("int.config", 1)
        assert config_tree == {'int': {'config': 1}}

    def test_overrides_int_with_config_append(self):
        config_tree = ConfigTree()
        config_tree.put("int", 5, True)
        config_tree.put("int.config", 1, True)
        assert config_tree == {'int': {'config': 1}}

    def test_plain_ordered_dict(self):
        config_tree = ConfigTree()
        config_tree.put('"a.b"', 5)
        config_tree.put('a."b.c"', [ConfigTree(), 2])
        config_tree.get('a."b.c"')[0].put('"c.d"', 1)
        d = OrderedDict()
        d['a.b'] = 5
        d['a'] = OrderedDict()
        d['a']['b.c'] = [OrderedDict(), 2]
        d['a']['b.c'][0]['c.d'] = 1
        assert config_tree.as_plain_ordered_dict() == d

    def test_contains(self):
        config_tree = ConfigTree()
        config_tree.put('a.b', 5)
        config_tree.put('a.c', None)
        assert 'a' in config_tree
        assert 'a.b' in config_tree
        assert 'a.c' in config_tree
        assert 'a.b.c' not in config_tree

    def test_contains_with_quoted_keys(self):
        config_tree = ConfigTree()
        config_tree.put('a.b."c.d"', 5)
        assert 'a' in config_tree
        assert 'a.b' in config_tree
        assert 'a.c' not in config_tree
        assert 'a.b."c.d"' in config_tree
        assert 'a.b.c.d' not in config_tree

    def test_configtree_pop(self):
        config_tree = ConfigTree()
        config_tree.put("string", "string")
        assert config_tree.pop("string", "default") == "string"
        assert config_tree.pop("string-new", "default") == "default"
        assert config_tree == ConfigTree()

        with pytest.raises(ConfigMissingException):
            assert config_tree.pop("string-new")

        config_tree.put("list", [1, 2, 3])
        assert config_tree.pop("list", [4]) == [1, 2, 3]
        assert config_tree.pop("list-new", [4]) == [4]
        assert config_tree == ConfigTree()

        config_tree.put("config", {'a': 5})
        assert config_tree.pop("config", {'b': 1}) == {'a': 5}
        assert config_tree.pop("config-new", {'b': 1}) == {'b': 1}
        assert config_tree == ConfigTree()

        config_tree = ConfigTree()
        config_tree.put('key', 'value')
        assert config_tree.pop('key', 'value') == 'value'
        assert 'key' not in config_tree

        config_tree = ConfigTree()
        config_tree.put('a.b.c.one', 1)
        config_tree.put('a.b.c.two', 2)
        config_tree.put('"f.k".g.three', 3)

        exp = OrderedDict()
        exp['a'] = OrderedDict()
        exp['a']['b'] = OrderedDict()
        exp['a']['b']['c'] = OrderedDict()
        exp['a']['b']['c']['one'] = 1
        exp['a']['b']['c']['two'] = 2

        exp['f.k'] = OrderedDict()
        exp['f.k']['g'] = OrderedDict()
        exp['f.k']['g']['three'] = 3

        assert config_tree.pop('a.b.c').as_plain_ordered_dict() == exp['a']['b']['c']
        assert config_tree.pop('a.b.c', None) is None

        with pytest.raises(ConfigMissingException):
            assert config_tree.pop('a.b.c')
        with pytest.raises(ConfigMissingException):
            assert config_tree['a']['b'].pop('c')

        assert config_tree.pop('a').as_plain_ordered_dict() == OrderedDict(b=OrderedDict())
        assert config_tree.pop('"f.k"').as_plain_ordered_dict() == OrderedDict(g=OrderedDict(three=3))
        assert config_tree.as_plain_ordered_dict() == OrderedDict()

    def test_keyerror_raised(self):
        config_tree = ConfigTree()
        config_tree.put("a", {'b': 5})

        with pytest.raises(KeyError):
            assert config_tree['c']

    def test_configmissing_raised(self):
        config_tree = ConfigTree()
        for getter in [
            config_tree.get,
            config_tree.get_bool,
            config_tree.get_config,
            config_tree.get_float,
            config_tree.get_int,
            config_tree.get_list,
            config_tree.get_string
        ]:
            with pytest.raises(ConfigMissingException):
                assert getter('missing_key')

    def test_config_tree_special_characters(self):
        special_characters = '$}[]:=+#`^?!@*&.'
        for char in special_characters:
            config_tree = ConfigTree()
            escaped_key = "\"test{char}key\"".format(char=char)
            key = "a.b.{escaped_key}".format(escaped_key=escaped_key)
            config_tree.put(key, "value")
            hocon_tree = HOCONConverter.to_hocon(config_tree)
            assert escaped_key in hocon_tree
            parsed_tree = ConfigFactory.parse_string(hocon_tree)
            assert parsed_tree.get(key) == "value"
