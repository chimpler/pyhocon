import pytest
from pyhocon.config_tree import ConfigTree
from pyhocon.exceptions import ConfigMissingException, ConfigWrongTypeException

try:  # pragma: no cover
    from collections import OrderedDict
except ImportError:  # pragma: no cover
    from ordereddict import OrderedDict


class TestConfigParser(object):

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
