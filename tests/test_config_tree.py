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
