import os
import re
from pyparsing import *
from pyhocon.config_tree import ConfigTree, ConfigSubstitution, ConfigList, ConfigValues
from pyhocon.exceptions import ConfigException, ConfigSubstitutionException


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
    def parse(content):
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
            return norm_string(tokens[0])

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
        def create_substitution(token, loc, tokens):
            substitution = ConfigSubstitution(token, loc, tokens)
            substitutions.append(substitution)
            return substitution

        ParserElement.setDefaultWhitespaceChars(' \t')

        dict_expr = Forward()
        list_expr = Forward()
        assign_expr = Forward()

        true_expr = Keyword("true", caseless=True).setParseAction(replaceWith(True))
        false_expr = Keyword("false", caseless=True).setParseAction(replaceWith(False))
        null_expr = Keyword("null", caseless=True).setParseAction(replaceWith(None))
        key = QuotedString('"', escChar='\\') | Word(alphanums + '._')

        eol = Word('\n\r').suppress()
        eol_comma = Word('\n\r,').suppress()
        comment = ((Literal('#') | Literal('//')) - SkipTo(eol)).suppress()
        number_expr = Regex('[+-]?(\d*\.\d+|\d+(\.\d+)?)([eE]\d+)?').setParseAction(convert_number)

        # multi line string using """
        # Using fix described in http://pyparsing.wikispaces.com/share/view/3778969
        multiline_string = Regex('""".*?"""', re.DOTALL | re.UNICODE).setParseAction(unescape_multi_string)
        # single quoted line string
        singleline_string = QuotedString(quoteChar='"', escChar='\\', multiline=True)
        # default string that takes the rest of the line until an optional comment
        # we support .properties multiline support which is like this:
        # line1  \
        # line2 \
        # so a backslash precedes the \n
        defaultline_string = Regex('[^\s,\$\{\}\[\]#]+(?=//)?').setParseAction(unescape_string)
        substitution_expr = Regex('\$\{[^\}]+\}').setParseAction(create_substitution)
        string_expr = multiline_string | singleline_string | substitution_expr | defaultline_string

        value_expr = number_expr | true_expr | false_expr | null_expr | string_expr | substitution_expr
        values_expr = Forward()
        # multiline if \ at the end of the line
        values_expr << ConcatenatedValueParser(value_expr - ZeroOrMore(value_expr | (Literal('\\').suppress() - Optional(comment) - eol)))

        list_expr << ListParser(Suppress('[') - ZeroOrMore(values_expr | eol_comma | comment) - Suppress(']')) - ZeroOrMore(list_expr)

        # for a dictionary : or = is optional
        # last zeroOrMore is because we can have t = {a:4} {b: 6} {c: 7} which is dictionary concatenation
        inside_dict_expr = ConfigTreeParser(ZeroOrMore(assign_expr | eol_comma | comment))
        dict_expr << Suppress('{') - inside_dict_expr + Suppress('}') - ZeroOrMore(dict_expr)
        assign_dict_expr = Suppress(Optional(oneOf(['=', ':']))) + dict_expr

        # special case when we have a value assignment where the string can potentially be the remainder of the line
        assign_value_or_list_expr = Suppress(oneOf(['=', ':'])) + (list_expr | values_expr | eol_comma)
        assign_expr << Group(key + (assign_dict_expr | assign_value_or_list_expr))

        # the file can be { ... } where {} can be omitted or []
        config_expr = ZeroOrMore(comment | eol) \
            + (list_expr | dict_expr | inside_dict_expr) \
            + ZeroOrMore(comment | eol_comma)
        config = config_expr.parseString(content, parseAll=True)[0]

        # if config consists in a list
        return config if isinstance(config, ConfigTree) else list(config)

    @staticmethod
    def _resolve_variable(config, variable, substitution):
        variable = substitution.variable
        try:
            return config.get(variable)
        except:
            # default to environment variable
            value = os.environ.get(variable)
            if value is None:
                raise ConfigSubstitutionException("Cannot resolve variable ${{{variable}}} on {loc}".format(variable=variable, loc=substitution.loc))
            return value

    @staticmethod
    def _resolve_substitutions(config, substitutions):
        resolution = {}
        for i in range(len(substitutions)):
            unresolved = False
            for substitution in substitutions:
                value = ConfigParser._resolve_variable(config)
                if isinstance(value, ConfigValues):
                    if value.value is None:
                        # if it still unresolved then ignore and wait for the next pass
                        unresolved = True
                    else:
                        value.value = ' '.join(value._tokens)
                        resolution[substitution] = value.value
                else:
                    resolution[substitution] = value

            if not unresolved:
                break


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
        return [ConfigList(token_list)]


class ConcatenatedValueParser(TokenConverter):

    def __init__(self, expr=None):
        super(ConcatenatedValueParser, self).__init__(expr)

    def postParse(self, instring, loc, token_list):
        # If all are strings with no substitution then concatenate the strings (no further variable resolution)
        found_substitution = next((True for token in token_list if isinstance(token, ConfigSubstitution)), False)
        if found_substitution:
            return ConfigValues(token_list)
        elif len(token_list) == 1:
            return token_list[0]
        else:
            return ' '.join(str(token) for token in token_list)

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
        for tokens in token_list:
            # key, value1, value2, ...
            key = tokens[0]
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
                        conf_value = list(value) if isinstance(value, list) else value
                        config_tree.put(key, conf_value)

        return config_tree
