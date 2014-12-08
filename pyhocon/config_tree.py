from pyparsing import TokenConverter, ParseResults
from pyhocon.exceptions import ConfigException, ConfigWrongTypeException, ConfigMissingException


class ConfigTreeParser(TokenConverter):

    def __init__(self, expr=None):
        super(ConfigTreeParser, self).__init__(expr)
        self.saveAsList = True

    def postParse(self, instring, loc, token_list):
        config_tree = ConfigTree()
        for token in token_list:
            # key, value
            if len(token) == 2:
                key, value = token
                conv_value = list(value) if isinstance(value, ParseResults) else value
                config_tree.put(key, conv_value)

        return config_tree


class ConfigTree(object):
    KEY_SEP = '.'

    def __init__(self):
        self._dictionary = {}

    def _merge_config_tree(self, a, b):
        """
        Merge config b into a
        :param a: target config
        :type a: ConfigTree
        :param b: source config
        :type b: ConfigTree
        :return: merged config a
        """
        for key, value in b._dictionary.items():
            # if key is in both a and b and both values are dictionary then merge it otherwise override it
            if key in a._dictionary.items() and isinstance(a._dictionary[key], ConfigTree) and isinstance(a._dictionary[key], ConfigTree):
                self._merge_dict(a._dictionary[key], b._dictionary[key])
            else:
                a._dictionary[key] = value

        return a

    def _put(self, key_path, value):
        key_elt = key_path[0]
        if len(key_path) == 1:
            # if value to set does not exist, override
            # if they are both configs then merge
            # if not then override
            if key_elt in self._dictionary and isinstance(self._dictionary[key_elt], ConfigTree) and isinstance(value, ConfigTree):
                self._merge_config_tree(self._dictionary[key_elt], value)
            else:
                self._dictionary[key_elt] = value
        else:
            next_config_tree = self._dictionary.get(key_elt)
            if not isinstance(next_config_tree, ConfigTree):
                # create a new dictionary or overwrite a previous value
                next_config_tree = ConfigTree()
                self._dictionary[key_elt] = next_config_tree
            next_config_tree._put(key_path[1:], value)

    def _get(self, key_path, key_index=0):
        key_elt = key_path[key_index]
        elt = self._dictionary.get(key_elt)

        if key_index == len(key_path) - 1:
            return elt

        if elt is None:
            raise ConfigMissingException("No configuration setting found for key {key}".format(key='.'.join(key_path[:key_index + 1])))
        elif isinstance(elt, ConfigTree):
            return elt._get(key_path, key_index + 1)
        else:
            raise ConfigWrongTypeException("{key} has type {type} rather than dict".format(key='.'.join(key_path[:key_index + 1]), type=type(elt).__name__))

    def put(self, key, value):
        self._put(key.split(ConfigTree.KEY_SEP), value)

    def get(self, key):
        return self._get(key.split(ConfigTree.KEY_SEP))

    def get_string(self, key):
        return str(self.get(key))

    def get_int(self, key):
        return int(self.get(key))

    def get_float(self, key):
        return float(self.get(key))

    def get_bool(self, key):
        return bool(self.get(key))

    def get_list(self, key):
        value = self.get(key)
        if isinstance(value, list):
            return value
        else:
            raise ConfigException("{key} has type '{type}' rather than 'list'".format(key=key, type=type(value).__name__))

    def get_config(self, key):
        value = self.get(key)
        if isinstance(value, ConfigTree):
            return value
        else:
            raise ConfigException("{key} has type '{type}' rather than 'config'".format(key=key, type=type(value).__name__))

    def items(self):
        return self._dictionary.items()

    def iteritems(self):
        return self._dictionary.iteritems()

    def iterkeys(self):
        return self._dictionary.iterkeys()

    def itervalues(self):
        return self._dictionary.itervalues()

    def __getitem__(self, item):
        val = self.get(item)
        if val is None:
            raise KeyError(item)

        return val

    def __contains__(self, item):
        return item in self._dictionary

    def __str__(self):
        return str(self._dictionary)

    def __repr__(self):
        return repr(self._dictionary)

    def __len__(self):
        return len(self._dictionary)
