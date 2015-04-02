from collections import OrderedDict
import re
from pyhocon.exceptions import ConfigException, ConfigWrongTypeException, ConfigMissingException


class ConfigTree(OrderedDict):
    KEY_SEP = '.'

    def __init__(self):
        super(ConfigTree, self).__init__()

    def _merge_config_tree(self, a, b):
        """Merge config b into a

        :param a: target config
        :type a: ConfigTree
        :param b: source config
        :type b: ConfigTree
        :return: merged config a
        """
        for key, value in b.items():
            # if key is in both a and b and both values are dictionary then merge it otherwise override it
            if key in list(a.items()) and isinstance(a[key], ConfigTree) and isinstance(a[key], ConfigTree):
                self._merge_dict(a[key], b[key])
            else:
                a[key] = value

        return a

    def _put(self, key_path, value, append=False):
        key_elt = key_path[0]
        if len(key_path) == 1:
            # if value to set does not exist, override
            # if they are both configs then merge
            # if not then override
            if key_elt in self and isinstance(self[key_elt], ConfigTree) and isinstance(value, ConfigTree):
                self._merge_config_tree(self[key_elt], value)
            elif append:
                l = self.get(key_elt)
                if isinstance(l, list):
                    l += value
                elif l is None:
                    self[key_elt] = value
                else:
                    raise ConfigWrongTypeException("Cannot concatenate the list {key}: {value} to {prev_value} of {type}".format(
                        key='.'.join(key_path),
                        value=value,
                        prev_value=l,
                        type=l.__class__.__name__)
                    )
            else:
                super(ConfigTree, self).__setitem__(key_elt, value)
        else:
            next_config_tree = super(ConfigTree, self).get(key_elt)
            if not isinstance(next_config_tree, ConfigTree):
                # create a new dictionary or overwrite a previous value
                next_config_tree = ConfigTree()
                self[key_elt] = next_config_tree
            next_config_tree._put(key_path[1:], value, append)

    def _get(self, key_path, key_index=0):
        key_elt = key_path[key_index]
        elt = super(ConfigTree, self).get(key_elt, self.UndefinedKey)

        if elt is self.UndefinedKey:
            raise ConfigMissingException("No configuration setting found for key {key}".format(key='.'.join(key_path[:key_index + 1])))

        if key_index == len(key_path) - 1:
            return elt
        elif isinstance(elt, ConfigTree):
            return elt._get(key_path, key_index + 1)
        else:
            raise ConfigWrongTypeException("{key} has type {type} rather than dict".format(key='.'.join(key_path[:key_index + 1]), type=type(elt).__name__))

    def _parse_key(self, str):
        """
        Split a key into path elements:
        - a.b.c => a, b, c
        - a."b.c" => a, "b.c"
        - a.b."c" => a, b, c (special case)
        :param str:
        :return:
        """
        tokens = re.findall('"[^"]+"|[^\.]+', str)
        return [t.strip('"') for t in tokens]

    def put(self, key, value, append=False):
        """Put a value in the tree (dot separated)

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :param value: value to put
        """
        self._put(self._parse_key(key), value, append)

    def get(self, key):
        """Get a value from the tree

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :return: value in the tree located at key
        """
        return self._get(self._parse_key(key))

    def get_string(self, key):
        """Return string representation of value found at key

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :return: string value
        :type return: basestring
        """
        return str(self.get(key))

    def get_int(self, key):
        """Return int representation of value found at key

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :return: int value
        :type return: int
        """
        return int(self.get(key))

    def get_float(self, key):
        """Return float representation of value found at key

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :return: float value
        :type return: float
        """
        return float(self.get(key))

    def get_bool(self, key):
        """Return boolean representation of value found at key

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :return: boolean value
        :type return: bool
        """
        return bool(self.get(key))

    def get_list(self, key):
        """Return list representation of value found at key

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :return: list value
        :type return: list
        """
        value = self.get(key)
        if isinstance(value, list):
            return value
        else:
            raise ConfigException("{key} has type '{type}' rather than 'list'".format(key=key, type=type(value).__name__))

    def get_config(self, key):
        """Return tree config representation of value found at key

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :return: config value
        :type return: ConfigTree
        """
        value = self.get(key)
        if isinstance(value, ConfigTree):
            return value
        else:
            raise ConfigException("{key} has type '{type}' rather than 'config'".format(key=key, type=type(value).__name__))

    def __getitem__(self, item):
        val = self.get(item)
        if val is self.UndefinedKey:
            raise KeyError(item)
        return val

    class UndefinedKey(object):
        pass


class ConfigList(list):
    def __init__(self, iterable):
        l = list(iterable)
        super(ConfigList, self).__init__(l)
        for index, value in enumerate(l):
            if isinstance(value, ConfigValues):
                value.parent = self
                value.index = index


class ConfigValues(object):
    def __init__(self, iterable):
        self.tokens = iterable
        self.parent = None
        self.key = None
        for index, token in enumerate(self.tokens):
            if isinstance(token, ConfigSubstitution):
                token.parent = self
                token.index = index

        # if the last token is an unquoted string then right strip it
        if isinstance(self.tokens[-1], ConfigUnquotedString):
            self.tokens[-1] = self.tokens[-1].rstrip()

    def has_substitution(self):
        return next((True for token in self.tokens if isinstance(token, ConfigSubstitution)), False)

    def transform(self):
        if self.has_substitution():
            return self

        if len(self.tokens) == 1:
            return self.tokens[0]

        return ''.join(token if isinstance(token, str) else str(token) + ' ' for token in self.tokens[:-1]) + str(self.tokens[-1])

    def put(self, index, value):
        self.tokens[index] = value


class ConfigSubstitution(object):
    def __init__(self, variable, ws):
        self.variable = variable
        self.ws = ws
        self.index = None
        self.parent = None


class ConfigUnquotedString(str):

    def __new__(cls, value):
        return super(ConfigUnquotedString, cls).__new__(cls, value)


class ConfigSlashString(str):

    def __new__(cls, value):
        return super(ConfigSlashString, cls).__new__(cls, value)
