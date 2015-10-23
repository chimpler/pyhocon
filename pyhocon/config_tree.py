from pyparsing import lineno
from pyparsing import col

try:  # pragma: no cover
    from collections import OrderedDict
except ImportError:  # pragma: no cover
    from ordereddict import OrderedDict
try:
    basestring
except NameError:
    basestring = str

import re
from .exceptions import ConfigException, ConfigWrongTypeException, ConfigMissingException


class UndefinedKey(object):
    pass


class ConfigTree(OrderedDict):
    KEY_SEP = '.'

    def __init__(self, *args, **kwds):
        super(ConfigTree, self).__init__(*args, **kwds)

        for key, value in self.items():
            if isinstance(value, ConfigValues):
                value.parent = self
                value.index = key

    @classmethod
    def _merge_config_tree(cls, a, b):
        """Merge config b into a

        :param a: target config
        :type a: ConfigTree
        :param b: source config
        :type b: ConfigTree
        :return: merged config a
        """
        for key, value in b.items():
            # if key is in both a and b and both values are dictionary then merge it otherwise override it
            if key in a and isinstance(a[key], ConfigTree) and isinstance(a[key], ConfigTree):
                cls._merge_config_tree(a[key], b[key])
            else:
                if isinstance(value, ConfigValues):
                    value.parent = a
                    value.key = key
                    value.overriden_value = a.get(key, None)
                a[key] = value

        return a

    def _put(self, key_path, value, append=False):
        key_elt = key_path[0]
        if len(key_path) == 1:
            # if value to set does not exist, override
            # if they are both configs then merge
            # if not then override
            if key_elt in self and isinstance(self[key_elt], ConfigTree) and isinstance(value, ConfigTree):
                ConfigTree._merge_config_tree(self[key_elt], value)
            elif append:
                # If we have t=1
                # and we try to put t.a=5 then t is replaced by {a: 5}
                l = self.get(key_elt, None)
                if isinstance(l, list):
                    l += value
                elif l is None:
                    self[key_elt] = value
                else:
                    raise ConfigWrongTypeException(
                        "Cannot concatenate the list {key}: {value} to {prev_value} of {type}".format(
                            key='.'.join(key_path),
                            value=value,
                            prev_value=l,
                            type=l.__class__.__name__)
                    )
            else:
                # if there was an override keep overide value
                if isinstance(value, ConfigValues):
                    value.parent = self
                    value.key = key_elt
                    value.overriden_value = self.get(key_elt, None)
                super(ConfigTree, self).__setitem__(key_elt, value)
        else:
            next_config_tree = super(ConfigTree, self).get(key_elt)
            if not isinstance(next_config_tree, ConfigTree):
                # create a new dictionary or overwrite a previous value
                next_config_tree = ConfigTree()
                self[key_elt] = next_config_tree
            next_config_tree._put(key_path[1:], value, append)

    def _get(self, key_path, key_index=0, default=UndefinedKey):
        key_elt = key_path[key_index]
        elt = super(ConfigTree, self).get(key_elt, UndefinedKey)

        if elt is UndefinedKey:
            if default is UndefinedKey:
                raise ConfigMissingException("No configuration setting found for key {key}".format(key='.'.join(key_path[:key_index + 1])))
            else:
                return default

        if key_index == len(key_path) - 1:
            return elt
        elif isinstance(elt, ConfigTree):
            return elt._get(key_path, key_index + 1, default)
        else:
            if default is UndefinedKey:
                raise ConfigWrongTypeException(
                    "{key} has type {type} rather than dict".format(key='.'.join(key_path[:key_index + 1]),
                                                                    type=type(elt).__name__))
            else:
                return default

    def _parse_key(self, str):
        """
        Split a key into path elements:
        - a.b.c => a, b, c
        - a."b.c" => a, QuotedKey("b.c")
        - "a" => a
        - a.b."c" => a, b, c (special case)
        :param str:
        :return:
        """
        tokens = re.findall('"[^"]+"|[^\.]+', str)
        return [token if '.' in token else token.strip('"') for token in tokens]

    def put(self, key, value, append=False):
        """Put a value in the tree (dot separated)

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :param value: value to put
        """
        self._put(self._parse_key(key), value, append)

    def get(self, key, default=UndefinedKey):
        """Get a value from the tree

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :param default: default value if key not found
        :type default: object
        :return: value in the tree located at key
        """
        return self._get(self._parse_key(key), 0, default)

    def get_string(self, key, default=UndefinedKey):
        """Return string representation of value found at key

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :param default: default value if key not found
        :type default: basestring
        :return: string value
        :type return: basestring
        """
        return str(self.get(key, default))

    def get_int(self, key, default=UndefinedKey):
        """Return int representation of value found at key

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :param default: default value if key not found
        :type default: int
        :return: int value
        :type return: int
        """
        return int(self.get(key, default))

    def get_float(self, key, default=UndefinedKey):
        """Return float representation of value found at key

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :param default: default value if key not found
        :type default: float
        :return: float value
        :type return: float
        """
        return float(self.get(key, default))

    def get_bool(self, key, default=UndefinedKey):
        """Return boolean representation of value found at key

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :param default: default value if key not found
        :type default: bool
        :return: boolean value
        :type return: bool
        """
        return bool(self.get(key, default))

    def get_list(self, key, default=UndefinedKey):
        """Return list representation of value found at key

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :param default: default value if key not found
        :type default: list
        :return: list value
        :type return: list
        """
        value = self.get(key, default)
        if isinstance(value, list):
            return value
        else:
            raise ConfigException(
                "{key} has type '{type}' rather than 'list'".format(key=key, type=type(value).__name__))

    def get_config(self, key, default=UndefinedKey):
        """Return tree config representation of value found at key

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :param default: default value if key not found
        :type default: config
        :return: config value
        :type return: ConfigTree
        """
        value = self.get(key, default)
        if isinstance(value, dict):
            return value
        else:
            raise ConfigException(
                "{key} has type '{type}' rather than 'config'".format(key=key, type=type(value).__name__))

    def __getitem__(self, item):
        val = self.get(item)
        if val is UndefinedKey:
            raise KeyError(item)
        return val

    def with_fallback(self, config):
        """
        return a new config with fallback on config
        :param config: config or filename of the config to fallback on
        :return: new config with fallback on config
        """
        if isinstance(config, ConfigTree):
            result = self._merge_config_tree(config, self)
        else:
            from . import ConfigFactory
            result = self._merge_config_tree(ConfigFactory.parse_file(config, resolve=False), self)

        from . import ConfigParser
        ConfigParser.resolve_substitutions(result)
        return result


class ConfigList(list):
    def __init__(self, iterable=[]):
        l = list(iterable)
        super(ConfigList, self).__init__(l)
        for index, value in enumerate(l):
            if isinstance(value, ConfigValues):
                value.parent = self
                value.key = index


class ConfigInclude(object):
    def __init__(self, tokens):
        self.tokens = tokens


class ConfigValues(object):
    def __init__(self, tokens, instring, loc):
        self.tokens = tokens
        self.parent = None
        self.key = None
        self._instring = instring
        self._loc = loc
        self.overriden_value = None

        for index, token in enumerate(self.tokens):
            if isinstance(token, ConfigSubstitution):
                token.parent = self
                token.index = index

        # no value return empty string
        if len(self.tokens) == 0:
            self.tokens = ['']

        # if the last token is an unquoted string then right strip it
        if isinstance(self.tokens[-1], ConfigUnquotedString):
            self.tokens[-1] = self.tokens[-1].rstrip()

    def has_substitution(self):
        return len(self.get_substitutions()) > 0

    def get_substitutions(self):
        return [token for token in self.tokens if isinstance(token, ConfigSubstitution)]

    def transform(self):
        def determine_type(token):
            return ConfigTree if isinstance(token, ConfigTree) else ConfigList if isinstance(token, list) else str

        def format_str(v):
            return '' if v is None else str(v)

        if self.has_substitution():
            return self

        # remove None tokens
        tokens = [token for token in self.tokens if token is not None]

        if not tokens:
            return None

        # check if all tokens are compatible
        first_tok_type = determine_type(tokens[0])
        for index, token in enumerate(tokens[1:]):
            tok_type = determine_type(token)
            if first_tok_type is not tok_type:
                raise ConfigWrongTypeException(
                    "Token '{token}' of type {tok_type} (index {index}) must be of type {req_tok_type} (line: {line}, col: {col})".format(
                        token=token,
                        index=index + 1,
                        tok_type=tok_type.__name__,
                        req_tok_type=first_tok_type.__name__,
                        line=lineno(self._loc, self._instring),
                        col=col(self._loc, self._instring)))

        if first_tok_type is ConfigTree:
            result = ConfigTree()
            for token in tokens:
                for key, val in token.items():
                    # update references for substituted contents
                    if isinstance(val, ConfigValues):
                        val.parent = result
                        val.key = key
                    result[key] = val
            return result
        elif first_tok_type is ConfigList:
            result = []
            main_index = 0
            for sublist in tokens:
                sublist_result = ConfigList()
                for token in sublist:
                    if isinstance(token, ConfigValues):
                        token.parent = result
                        token.key = main_index
                    main_index += 1
                    sublist_result.append(token)
                result.extend(sublist_result)
            return [result]
        else:
            if len(tokens) == 1:
                return tokens[0]
            else:
                return ''.join(
                    token if isinstance(token, basestring) else format_str(token) + ' ' for token in tokens[:-1]) + format_str(tokens[-1])

    def put(self, index, value):
        self.tokens[index] = value

    def __repr__(self):  # pragma: no cover
        return '[ConfigValues: ' + ','.join(str(o) for o in self.tokens) + ']'


class ConfigSubstitution(object):
    def __init__(self, variable, optional, ws, instring, loc):
        self.variable = variable
        self.optional = optional
        self.ws = ws
        self.index = None
        self.parent = None
        self.instring = instring
        self.loc = loc

    def __repr__(self):  # pragma: no cover
        return '[ConfigSubstitution: ' + self.variable + ']'


class ConfigUnquotedString(str):
    def __new__(cls, value):
        return super(ConfigUnquotedString, cls).__new__(cls, value)
