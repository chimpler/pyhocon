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
from pyhocon.exceptions import ConfigException, ConfigWrongTypeException, ConfigMissingException


class UndefinedKey(object):
    pass


class NoneValue(object):
    pass


class ConfigTree(OrderedDict):
    KEY_SEP = '.'

    def __init__(self, *args, **kwds):
        self.root = kwds.pop('root') if 'root' in kwds else False
        if self.root:
            self.history = {}
        super(ConfigTree, self).__init__(*args, **kwds)
        for key, value in self.items():
            if isinstance(value, ConfigValues):
                value.parent = self
                value.index = key

    @staticmethod
    def merge_configs(a, b, copy_trees=False):
        """Merge config b into a

        :param a: target config
        :type a: ConfigTree
        :param b: source config
        :type b: ConfigTree
        :return: merged config a
        """
        for key, value in b.items():
            # if key is in both a and b and both values are dictionary then merge it otherwise override it
            if key in a and isinstance(a[key], ConfigTree) and isinstance(b[key], ConfigTree):
                if copy_trees:
                    a[key] = a[key].copy()
                ConfigTree.merge_configs(a[key], b[key], copy_trees=copy_trees)
            else:
                if isinstance(value, ConfigValues):
                    value.parent = a
                    value.key = key
                    value.overriden_value = a.get(key, None)
                a[key] = value
                if a.root:
                    a.history[key] = (a.history.get(key) or []) + b.history.get(key)

        return a

    def _put(self, key_path, value, append=False):
        key_elt = key_path[0]
        if len(key_path) == 1:
            # if value to set does not exist, override
            # if they are both configs then merge
            # if not then override
            if key_elt in self and isinstance(self[key_elt], ConfigTree) and isinstance(value, ConfigTree):
                if self.root:
                    new_value = ConfigTree.merge_configs(ConfigTree(), self[key_elt], copy_trees=True)
                    new_value = ConfigTree.merge_configs(new_value, value, copy_trees=True)
                    self._push_history(key_elt, new_value)
                    self[key_elt] = new_value
                else:
                    ConfigTree.merge_configs(self[key_elt], value)
            elif append:
                # If we have t=1
                # and we try to put t.a=5 then t is replaced by {a: 5}
                l = self.get(key_elt, None)
                if isinstance(l, ConfigValues):
                    l.tokens.append(value)
                    l.recompute()
                elif isinstance(l, ConfigTree) and isinstance(value, ConfigValues):
                    value.tokens.append(l)
                    value.recompute()
                    self._push_history(key_elt, value)
                    self[key_elt] = value
                elif isinstance(l, list) and isinstance(value, ConfigValues):
                    self._push_history(key_elt, value)
                    self[key_elt] = value
                elif isinstance(l, list):
                    l += value
                    self._push_history(key_elt, l)
                elif l is None:
                    self._push_history(key_elt, value)
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
                self._push_history(key_elt, value)
                self[key_elt] = value
        else:
            next_config_tree = super(ConfigTree, self).get(key_elt)
            if not isinstance(next_config_tree, ConfigTree):
                # create a new dictionary or overwrite a previous value
                next_config_tree = ConfigTree()
                self._push_history(key_elt, value)
                self[key_elt] = next_config_tree
            next_config_tree._put(key_path[1:], value, append)

    def _push_history(self, key, value):
        if self.root:
            hist = self.history.get(key)
            if hist is None:
                hist = self.history[key] = []
            hist.append(value)

    def _get(self, key_path, key_index=0, default=UndefinedKey):
        key_elt = key_path[key_index]
        elt = super(ConfigTree, self).get(key_elt, UndefinedKey)

        if elt is UndefinedKey:
            if default is UndefinedKey:
                raise ConfigMissingException("No configuration setting found for key {key}".format(key='.'.join(key_path[:key_index + 1])))
            else:
                return default

        if key_index == len(key_path) - 1:
            if isinstance(elt, NoneValue):
                return None
            else:
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

    @staticmethod
    def parse_key(str):
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
        self._put(ConfigTree.parse_key(key), value, append)

    def get(self, key, default=UndefinedKey):
        """Get a value from the tree

        :param key: key to use (dot separated). E.g., a.b.c
        :type key: basestring
        :param default: default value if key not found
        :type default: object
        :return: value in the tree located at key
        """
        return self._get(ConfigTree.parse_key(key), 0, default)

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
            result = ConfigTree.merge_configs(config, self)
        else:
            from . import ConfigFactory
            result = ConfigTree.merge_configs(ConfigFactory.parse_file(config, resolve=False), self)

        from . import ConfigParser
        ConfigParser.resolve_substitutions(result)
        return result

    def as_plain_ordered_dict(self):
        """return a deep copy of this config as a plain OrderedDict

        The config tree should be fully resolved.

        This is useful to get an object with no special semantics such as path expansion for the keys.
        In particular this means that keys that contain dots are not surrounded with '"' in the plain OrderedDict.

        :return: this config as an OrderedDict
        :type return: OrderedDict
        """
        def plain_value(v):
            if isinstance(v, list):
                return [plain_value(e) for e in v]
            elif isinstance(v, ConfigTree):
                return v.as_plain_ordered_dict()
            else:
                if isinstance(v, ConfigValues):
                    raise ConfigException("The config tree contains unresolved elements")
                return v

        return OrderedDict((key.strip('"'), plain_value(value)) for key, value in self.items())


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
        self.recompute()

    def recompute(self):
        for index, token in enumerate(self.tokens):
            if isinstance(token, ConfigSubstitution):
                token.parent = self
                token.index = index

        # no value return empty string
        if len(self.tokens) == 0:
            self.tokens = ['']

        # if the last token is an unquoted string then right strip it
        if isinstance(self.tokens[-1], ConfigUnquotedString):
            # rstrip only whitespaces, not \n\r because they would have been used escaped
            self.tokens[-1] = self.tokens[-1].rstrip(' \t')

    def has_substitution(self):
        return len(self.get_substitutions()) > 0

    def get_substitutions(self):
        return [token for token in self.tokens if isinstance(token, ConfigSubstitution)]

    def transform(self):
        def determine_type(token):
            return ConfigTree if isinstance(token, ConfigTree) else ConfigList if isinstance(token, list) else str

        def format_str(v, last=False):
            if isinstance(v, ConfigQuotedString):
                return v.value + ('' if last else v.ws)
            else:
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
                ConfigTree.merge_configs(result, token, copy_trees=True)
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
            return result
        else:
            if len(tokens) == 1:
                if isinstance(tokens[0], ConfigQuotedString):
                    return tokens[0].value
                return tokens[0]
            else:
                return ''.join(format_str(token) for token in tokens[:-1]) + format_str(tokens[-1], True)

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


class ConfigQuotedString(object):
    def __init__(self, value, ws, instring, loc):
        self.value = value
        self.ws = ws
        self.instring = instring
        self.loc = loc

    def __repr__(self):  # pragma: no cover
        return '[ConfigQuotedString: ' + self.value + ']'
