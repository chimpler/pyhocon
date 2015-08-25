import re
import os
import socket
from pyparsing import Forward, Keyword, QuotedString, Word, Literal, Suppress, Regex, Optional, SkipTo, ZeroOrMore, \
    Group, lineno, col, TokenConverter, replaceWith, alphanums
from pyparsing import ParserElement
from .config_tree import ConfigTree, ConfigSubstitution, ConfigList, ConfigValues, ConfigUnquotedString, \
    ConfigInclude
from .exceptions import ConfigSubstitutionException, ConfigMissingException
import logging


use_urllib2 = False
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
    from urllib.error import HTTPError
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen, HTTPError

    use_urllib2 = True


logger = logging.getLogger(__name__)


class ConfigFactory(object):
    @staticmethod
    def parse_file(filename, required=True, resolve=True):
        """Parse file

        :param filename: filename
        :type filename: basestring
        :param required: If true, raises an exception if can't load file
        :type required: boolean
        :param resolve: If true, resolve substitutions
        :type resolve: boolean
        :return: Config object
        :type return: Config
        """
        try:
            with open(filename, 'r') as fd:
                content = fd.read()
                return ConfigFactory.parse_string(content, os.path.dirname(filename), resolve)
        except IOError as e:
            if required:
                raise e
            logger.warn('Cannot include file %s. File does not exist or cannot be read.', filename)
            return []

    @staticmethod
    def parse_URL(url, timeout=None, resolve=True):
        """Parse URL

        :param url: url to parse
        :type url: basestring
        :param resolve: If true, resolve substitutions
        :type resolve: boolean
        :return: Config object
        :type return: Config
        """
        socket_timeout = socket._GLOBAL_DEFAULT_TIMEOUT if timeout is None else timeout
        try:
            fd = urlopen(url, timeout=socket_timeout)
            content = fd.read() if use_urllib2 else fd.read().decode('utf-8')
            return ConfigFactory.parse_string(content, os.path.dirname(url), resolve)
        except HTTPError:
            logger.warn('Cannot include url %s. Resource is inaccessible.', url)
        finally:
            fd.close()

    @staticmethod
    def parse_string(content, basedir=None, resolve=True):
        """Parse URL

        :param content: content to parse
        :type content: basestring
        :param resolve: If true, resolve substitutions
        :type resolve: boolean
        :return: Config object
        :type return: Config
        """
        return ConfigParser().parse(content, basedir, resolve)

    @staticmethod
    def from_dict(dictionary):
        """Convert dictionary (and ordered dictionary) into a ConfigTree
        :param dictionary: dictionary to convert
        :type dictionary: dict
        :return: Config object
        :type return: Config
        """
        def __dCpList__(inp):
            for vl in inp:
                if isinstance(vl, list):
                    yield list(__dCpList__(vl))
                elif isinstance(vl, dict):
                    yield __dCpDict__(vl)

        def __dCpDict__(inp):
            outp = inp.copy()
            for ky, vl in outp.iteritems():
                if isinstance(vl, dict):
                    outp[ky] = __dCpDict__(vl)      
                elif isinstance(vl, list):
                    outp[ky] = list(__dCpList__(vl))  
            return ConfigTree(outp)

        def __simpleDCp__(inp):
            if isinstance(inp, dict):
                return __dCpDict__(inp)
            elif isinstance(inp, list):
                return __dCpList__(inp)
            else:
                return inp
        return __simpleDCp__(dictionary)


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
    def parse(content, basedir=None, resolve=True):
        """parse a HOCON content

        :param content: HOCON content to parse
        :type content: basestring
        :param resolve: If true, resolve substitutions
        :type resolve: boolean
        :return: a ConfigTree or a list
        """

        def norm_string(value):
            for k, v in ConfigParser.REPLACEMENTS.items():
                value = value.replace(k, v)
            return value

        def unescape_string(tokens):
            return ConfigUnquotedString(norm_string(tokens[0]))

        def parse_multi_string(tokens):
            # remove the first and last 3 "
            return tokens[0][3: -3]

        def convert_number(tokens):
            n = tokens[0]
            try:
                return int(n)
            except ValueError:
                return float(n)

        # ${path} or ${?path} for optional substitution
        SUBSTITUTION = "\$\{(?P<optional>\?)?(?P<variable>[^}]+)\}(?P<ws>\s*)"

        def create_substitution(instring, loc, token):
            # remove the ${ and }
            match = re.match(SUBSTITUTION, token[0])
            variable = match.group('variable')
            ws = match.group('ws')
            optional = match.group('optional') == '?'
            substitution = ConfigSubstitution(variable, optional, ws, instring, loc)
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
                logger.debug('Loading config from url %s', url)
                obj = ConfigFactory.parse_URL(url, resolve=False)

            if file is not None:
                path = file if basedir is None else os.path.join(basedir, file)
                logger.debug('Loading config from file %s', path)
                obj = ConfigFactory.parse_file(path, required=False, resolve=False)

            return ConfigInclude(obj if isinstance(obj, list) else obj.items())

        ParserElement.setDefaultWhitespaceChars(' \t')

        assign_expr = Forward()
        true_expr = Keyword("true", caseless=True).setParseAction(replaceWith(True))
        false_expr = Keyword("false", caseless=True).setParseAction(replaceWith(False))
        null_expr = Keyword("null", caseless=True).setParseAction(replaceWith(None))
        key = QuotedString('"', escChar='\\', unquoteResults=False) | Word(alphanums + '._- ')

        eol = Word('\n\r').suppress()
        eol_comma = Word('\n\r,').suppress()
        comment = (Literal('#') | Literal('//')) - SkipTo(eol)
        comment_eol = Suppress(Optional(eol_comma) + comment)
        comment_no_comma_eol = (comment | eol).suppress()
        number_expr = Regex('[+-]?(\d*\.\d+|\d+(\.\d+)?)([eE]\d+)?(?=[ \t]*([\$\}\],#\n\r]|//))',
                            re.DOTALL).setParseAction(convert_number)

        # multi line string using """
        # Using fix described in http://pyparsing.wikispaces.com/share/view/3778969
        multiline_string = Regex('""".*?"""', re.DOTALL | re.UNICODE).setParseAction(parse_multi_string)
        # single quoted line string
        quoted_string = QuotedString(quoteChar='"', escChar='\\', multiline=True)
        # unquoted string that takes the rest of the line until an optional comment
        # we support .properties multiline support which is like this:
        # line1  \
        # line2 \
        # so a backslash precedes the \n
        unquoted_string = Regex(r'(\\[ \t]*[\r\n]|[^\[\{\n\]\}#,=\$])+?(?=(\$|[ \t]*(//|[\}\],#\n\r])))',
                                re.DOTALL).setParseAction(unescape_string)
        substitution_expr = Regex('\$\{[^\}]+\}[ \t]*').setParseAction(create_substitution)
        string_expr = multiline_string | quoted_string | unquoted_string

        value_expr = number_expr | true_expr | false_expr | null_expr | string_expr

        include_expr = (Keyword("include", caseless=True).suppress() - (
            quoted_string | ((Keyword('url') | Keyword('file')) - Literal('(').suppress() - quoted_string - Literal(')').suppress()))) \
            .setParseAction(include_config)

        dict_expr = Forward()
        list_expr = Forward()
        multi_value_expr = ZeroOrMore((Literal(
            '\\') - eol).suppress() | comment_eol | include_expr | substitution_expr | dict_expr | list_expr | value_expr)
        # for a dictionary : or = is optional
        # last zeroOrMore is because we can have t = {a:4} {b: 6} {c: 7} which is dictionary concatenation
        inside_dict_expr = ConfigTreeParser(ZeroOrMore(comment_eol | include_expr | assign_expr | eol_comma))
        dict_expr << Suppress('{') - inside_dict_expr - Suppress('}')
        list_entry = ConcatenatedValueParser(multi_value_expr)
        list_expr << Suppress('[') - ListParser(list_entry - ZeroOrMore(eol_comma - list_entry)) - Suppress(']')

        # special case when we have a value assignment where the string can potentially be the remainder of the line
        assign_expr << Group(
            key -
            ZeroOrMore(comment_no_comma_eol) -
            (dict_expr | Suppress(Literal('=') | Literal(':')) - ZeroOrMore(comment_no_comma_eol) - ConcatenatedValueParser(multi_value_expr))
        )

        # the file can be { ... } where {} can be omitted or []
        config_expr = ZeroOrMore(comment_eol | eol) + (list_expr | dict_expr | inside_dict_expr) + ZeroOrMore(comment_eol | eol_comma)
        config = config_expr.parseString(content, parseAll=True)[0]
        if resolve:
            ConfigParser.resolve_substitutions(config)
        return config

    @staticmethod
    def _resolve_variable(config, substitution):
        """
        :param config:
        :param substitution:
        :return: (is_resolved, resolved_variable)
        """
        variable = substitution.variable
        try:
            return True, config.get(variable)
        except ConfigMissingException:
            # default to environment variable
            value = os.environ.get(variable)

            if value is None:
                if substitution.optional:
                    return False, None
                else:
                    raise ConfigSubstitutionException(
                        "Cannot resolve variable ${{{variable}}} (line: {line}, col: {col})".format(
                            variable=variable,
                            line=lineno(substitution.loc, substitution.instring),
                            col=col(substitution.loc, substitution.instring)))
            elif isinstance(value, ConfigList) or isinstance(value, ConfigTree):
                raise ConfigSubstitutionException(
                    "Cannot substitute variable ${{{variable}}} because it does not point to a "
                    "string, int, float, boolean or null {type} (line:{line}, col: {col})".format(
                        variable=variable,
                        type=value.__class__.__name__,
                        line=lineno(substitution.loc, substitution.instring),
                        col=col(substitution.loc, substitution.instring)))
            return True, value

    @staticmethod
    def resolve_substitutions(config):
        # traverse config to find all the substitutions
        def find_substitutions(item):
            """Convert HOCON input into a JSON output

            :return: JSON string representation
            :type return: basestring
            """
            if isinstance(item, ConfigValues):
                return item.get_substitutions()

            substitutions = []
            if isinstance(item, ConfigTree):
                    for key, child in item.items():
                        substitutions += find_substitutions(child)
            elif isinstance(item, list):
                for child in item:
                    substitutions += find_substitutions(child)

            return substitutions

        substitutions = find_substitutions(config)

        if len(substitutions) > 0:
            _substitutions = set(substitutions)
            for i in range(len(substitutions)):
                unresolved = False
                for substitution in list(_substitutions):
                    is_optional_resolved, resolved_value = ConfigParser._resolve_variable(config, substitution)

                    # if the substitution is optional
                    if not is_optional_resolved and substitution.optional:
                        resolved_value = None

                    if isinstance(resolved_value, ConfigValues):
                        unresolved = True
                    else:
                        # replace token by substitution
                        config_values = substitution.parent
                        # if it is a string, then add the extra ws that was present in the original string after the substitution
                        formatted_resolved_value = \
                            resolved_value + substitution.ws \
                            if isinstance(resolved_value, str) and substitution.index < len(config_values.tokens) - 1 else resolved_value
                        config_values.put(substitution.index, formatted_resolved_value)
                        transformation = config_values.transform()
                        if transformation is None and not is_optional_resolved:
                            # if it does not override anything remove the key
                            # otherwise put back old value that it was overriding
                            if config_values.overriden_value is None:
                                del config_values.parent[config_values.key]
                            else:
                                config_values.parent[config_values.key] = config_values.overriden_value
                        else:
                            result = transformation[0] if isinstance(transformation, list) else transformation
                            config_values.parent[config_values.key] = result
                        _substitutions.remove(substitution)
                if not unresolved:
                    break
            else:
                raise ConfigSubstitutionException("Cannot resolve {variables}. Check for cycles.".format(
                    variables=', '.join('${{{variable}}}: (line: {line}, col: {col})'.format(
                        variable=substitution.variable,
                        line=lineno(substitution.loc, substitution.instring),
                        col=col(substitution.loc, substitution.instring)) for substitution in _substitutions)))

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
        cleaned_token_list = [token for tokens in (token.tokens if isinstance(token, ConfigInclude) else [token]
                                                   for token in token_list if token != '')
                              for token in tokens]
        config_list = ConfigList(cleaned_token_list)
        return [config_list]


class ConcatenatedValueParser(TokenConverter):
    def __init__(self, expr=None):
        super(ConcatenatedValueParser, self).__init__(expr)
        self.parent = None
        self.key = None

    def postParse(self, instring, loc, token_list):
        config_values = ConfigValues(token_list, instring, loc)
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
            expanded_tokens = element.tokens if isinstance(element, ConfigInclude) else [element]

            for tokens in expanded_tokens:
                # key, value1 (optional), ...
                key = tokens[0].strip()
                values = tokens[1:]

                # empty string
                if len(values) == 0:
                    config_tree.put(key, '')
                else:
                    value = values[0]
                    if isinstance(value, list):
                        config_tree.put(key, value, False)
                    else:
                        # Merge dict
                        if isinstance(value, ConfigValues):
                            conf_value = value
                            value.parent = config_tree
                            value.key = key
                        else:
                            conf_value = value
                        config_tree.put(key, conf_value)
        return config_tree
