import pytest
from pyhocon.config_tree import ConfigTree
from pyhocon.exceptions import ConfigException


class TestConfigParser(object):

    def test_config_tree_quoted_string(self):
        config_tree = ConfigTree()
        config_tree.put("a.b.c", "value")
        assert config_tree.get("a.b.c") == "value"
        assert config_tree.get("a.b.d") is None
        with pytest.raises(ConfigException):
            config_tree.get("a.d.e")

    def test_config_tree_number(self):
        config_tree = ConfigTree()
        config_tree.put("a.b.c", 5)
        assert config_tree.get("a.b.c") == 5
