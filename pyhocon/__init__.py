import re
import os
import socket
import urllib2
from pyhocon.config_tree import ConfigTree, ConfigSubstitution, ConfigList, ConfigValues, ConfigUnquotedString
from pyhocon.exceptions import ConfigSubstitutionException
from pyparsing import *


class ConfigFactory(object):
    @staticmethod
    def parse_file(filename):
        """Parse file

        :param filename: filename
        :type filename: basestring
        :return: Config object
        :type return: Config
        """
        with open(filename, 'r') as fd:
            content = fd.read()
            return ConfigFactory.parse_string(content, os.path.dirname(filename))

    @staticmethod
    def parse_URL(url, timeout=None):
        """Parse URL

        :param url: url to parse
        :type url: basestring
        :return: Config object
        :type return: Config
        """
        socket_timeout = socket._GLOBAL_DEFAULT_TIMEOUT if timeout is None else timeout
        fd = urllib2.urlopen(url, timeout=socket_timeout)
        try:
            content = fd.read()
            return ConfigFactory.parse_string(content, os.path.dirname(url))
        finally:
            fd.close()

    @staticmethod
    def parse_string(content, basedir=None):
        """Parse URL

        :param url: url to parse
        :type url: basestring
        :return: Config object
        :type return: Config
        """
        return ConfigParser().parse(content, basedir)


class ConfigParser(object):
    """
    Parse HOCON files: https://github.com/typesafehub/config/blob/master/HOCON.md
    """

    REPLACEMENTS = {
        '\\\n': '\n',
        '\\n': '\n',
        '\\r': '\r',
        '\\t': '\t',
        '\\=': '=',
        '\\#': '#',
        '\\!': '!',
        '\\"': '"'
    }

    @staticmethod
    def parse(content, basedir=None):
        """parse a HOCON content

        :param content: HOCON content to parse
        :type content: basestring
        :return: a ConfigTree or a list
        """
        def norm_string(value):
            for k, v in ConfigParser.REPLACEMENTS.items():
                value = value.replace(k, v)
            return value

        def unescape_string(tokens):
            return ConfigUnquotedString(norm_string(tokens[0]))

        def unescape_multi_string(tokens):
            # remove the first and last 3 "
            return norm_string(tokens[0][3: -3])

        def convert_number(tokens):
            n = tokens[0]
            try:
                return int(n)
            except ValueError:
                return float(n)

        substitutions = []
        SUBSTITUTION = "\$\{(?P<variable>[^}]+)\}(?P<ws>\s*)"

        def create_substitution(token):
            # remove the ${ and }
            match = re.match(SUBSTITUTION, token[0])
            variable = match.group('variable')
            ws = match.group('ws')
            substitution = ConfigSubstitution(variable, ws)
            substitutions.append(substitution)
            return substitution

        def include_config(token):
            url = None
            file = None
            if len(token) == 1:  # include "test"
                if token[0].startswith("http://") or token[0].startswith("https://") or token[0].startswith("file://"):
                    url = token[0]
                else:
                    file = token[0]
            elif len(token) == 2:  # include url("test") or file("test")
                if token[0] == 'url':
                    url = token[1]
                else:
                    file = token[1]

            if url is not None:
                obj = ConfigFactory.parse_URL(url)

            if file is not None:
                path = file if basedir is None else os.path.join(basedir, file)
                obj = ConfigFactory.parse_file(path)

            return [obj]

        ParserElement.setDefaultWhitespaceChars(' \t')

        dict_expr = Forward()
        list_expr = Forward()
        assign_expr = Forward()

        true_expr = Keyword("true", caseless=True).setParseAction(replaceWith(True))
        false_expr = Keyword("false", caseless=True).setParseAction(replaceWith(False))
        null_expr = Keyword("null", caseless=True).setParseAction(replaceWith(None))
        key = QuotedString('"', escChar='\\', unquoteResults=False) | Word(alphanums + '._- ')

        eol = Word('\n\r').suppress()
        eol_comma = Word('\n\r,').suppress()
        comment = (Optional(eol_comma) + (Literal('#') | Literal('//')) - SkipTo(eol)).suppress()
        number_expr = Regex('[+-]?(\d*\.\d+|\d+(\.\d+)?)([eE]\d+)?(?=[ \t]*([\$\}\],#\n\r]|//))', re.DOTALL).setParseAction(convert_number)

        # multi line string using """
        # Using fix described in http://pyparsing.wikispaces.com/share/view/3778969
        multiline_string = Regex('""".*?"""', re.DOTALL | re.UNICODE).setParseAction(unescape_multi_string)
        # single quoted line string
        quoted_string = QuotedString(quoteChar='"', escChar='\\', multiline=True)
        # unquoted string that takes the rest of the line until an optional comment
        # we support .properties multiline support which is like this:
        # line1  \
        # line2 \
        # so a backslash precedes the \n
        unquoted_string = Regex(r'(\\[ \t]*[\r\n]|[^\[\{\n\]\}#,=\$])+?(?=(\$|[ \t]*(//|[\}\],#\n\r])))', re.DOTALL).setParseAction(unescape_string)
        substitution_expr = Regex('\$\{[^\}]+\}\s*').setParseAction(create_substitution)
        string_expr = multiline_string | quoted_string | unquoted_string

        value_expr = number_expr | true_expr | false_expr | null_expr | string_expr | substitution_expr
        values_expr = ConcatenatedValueParser(value_expr - ZeroOrMore(comment | (value_expr - Optional(Literal('\\') - eol).suppress()) | value_expr))
        # multiline if \ at the end of the line

        list_expr << ListParser(Suppress('[') - ZeroOrMore(comment | values_expr | eol_comma) - Suppress(']')) - ZeroOrMore(list_expr)

        include_expr = (Keyword("include", caseless=True).suppress() - (
            quoted_string | ((Keyword('url') | Keyword('file')) - Literal('(').suppress() - quoted_string - Literal(')').suppress())))\
            .setParseAction(include_config)

        # for a dictionary : or = is optional
        # last zeroOrMore is because we can have t = {a:4} {b: 6} {c: 7} which is dictionary concatenation
        inside_dict_expr = ConfigTreeParser(ZeroOrMore(comment | include_expr | assign_expr | eol_comma))
        dict_expr << Suppress('{') - inside_dict_expr + Suppress('}') - ZeroOrMore(dict_expr)
        assign_dict_expr = Suppress(Optional(oneOf(['=', ':']))) + dict_expr

        # special case when we have a value assignment where the string can potentially be the remainder of the line
        assign_value_or_list_expr = Suppress(oneOf(['=', ':'])) + (comment | list_expr | values_expr | eol_comma)
        assign_expr << Group(key + (assign_dict_expr | assign_value_or_list_expr))

        # the file can be { ... } where {} can be omitted or []
        config_expr = ZeroOrMore(comment | eol) \
            + (list_expr | dict_expr | inside_dict_expr) \
            + ZeroOrMore(comment | eol_comma)
        config = config_expr.parseString(content, parseAll=True)[0]
        ConfigParser._resolve_substitutions(config, substitutions)
        return config

    @staticmethod
    def _resolve_variable(config, substitution):
        variable = substitution.variable
        try:
            return config.get(variable)
        except:
            # default to environment variable
            value = os.environ.get(variable)
            if value is None:
                raise ConfigSubstitutionException("Cannot resolve variable ${{{variable}}}".format(variable=variable))
            elif isinstance(value, ConfigList) or isinstance(value, ConfigTree):
                raise ConfigSubstitutionException(
                    "Cannot substitute variable ${{{variable}}} because it does not point to a string, int, float, boolean or null (type)".format(
                        variable=variable,
                        type=value.__class__.__name__)
                )
            return value

    @staticmethod
    def _resolve_substitutions(config, substitutions):
        if len(substitutions) > 0:
            _substitutions = set(substitutions)
            for i in range(len(substitutions)):
                unresolved = False
                for substitution in list(_substitutions):
                    resolved_value = ConfigParser._resolve_variable(config, substitution)
                    if isinstance(resolved_value, ConfigValues):
                        unresolved = True
                    else:
                        # replace token by substitution
                        config_values = substitution.parent
                        # if there is more than one element in the config values then it's a string

                        tokens = substitution.parent.tokens
                        config_values.put(substitution.index, resolved_value)
                        config_values.parent[config_values.key] = config_values.transform()
                        _substitutions.remove(substitution)
                if not unresolved:
                    break
            else:
                raise ConfigSubstitutionException("Cannot resolve {variables}. Check for cycles.".format(
                    variables=', '.join('${' + substitution.variable + '}' for substitution in _substitutions)
                ))

        return config


class ListParser(TokenConverter):
    """Parse a list [elt1, etl2, ...]
    """

    def __init__(self, expr=None):
        super(ListParser, self).__init__(expr)
        self.saveAsList = True

    def postParse(self, instring, loc, token_list):
        """Create a list from the tokens

        :param instring:
        :param loc:
        :param token_list:
        :return:
        """
        config_list = ConfigList(token_list)
        return [config_list]


class ConcatenatedValueParser(TokenConverter):

    def __init__(self, expr=None):
        super(ConcatenatedValueParser, self).__init__(expr)
        self.parent = None
        self.key = None

    def postParse(self, instring, loc, token_list):
        config_values = ConfigValues(token_list)
        return config_values.transform()


class ConfigTreeParser(TokenConverter):
    """
    Parse a config tree from tokens
    """
    def __init__(self, expr=None):
        super(ConfigTreeParser, self).__init__(expr)
        self.saveAsList = True

    def postParse(self, instring, loc, token_list):
        """Create ConfigTree from tokens

        :param instring:
        :param loc:
        :param token_list:
        :return:
        """
        config_tree = ConfigTree()
        for element in token_list:
            # from include then merge items
            expanded_tokens = element._dictionary.iteritems() if isinstance(element, ConfigTree) else [element]

            for tokens in expanded_tokens:
                # key, value1, value2, ...
                key = tokens[0].strip()
                values = tokens[1:]

                # empty string
                if len(values) == 0:
                    config_tree.put(key, '')
                else:
                    if isinstance(values[0], list):
                        # Merge arrays
                        config_tree.put(key, values[0], False)
                        for value in values[1:]:
                            config_tree.put(key, value, True)
                    else:
                        # Merge dict
                        for value in values:
                            if isinstance(value, ConfigList):
                                conf_value = list(value)
                            elif isinstance(value, ConfigValues):
                                conf_value = value
                                value.parent = config_tree
                                value.key = key
                            else:
                                conf_value = value
                            config_tree.put(key, conf_value)

        return config_tree
