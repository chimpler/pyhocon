import pytest
from pyhocon.config_tree import ConfigTree
from pyhocon.exceptions import ConfigMissingException, ConfigWrongTypeException


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
        assert config_tree.get("a.b.c") == 5

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
