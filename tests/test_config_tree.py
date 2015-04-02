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
        logging.config.dictConfig(config_tree)

    def test_config_tree_null(self):
        config_tree = ConfigTree()
        config_tree.put("a.b.c", None)
        assert config_tree.get("a.b.c") is None
