import re
from pyparsing import *
from pyhocon.config_tree import ConfigTree
from pyhocon.exceptions import ConfigException


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

        def unescape_quoted_string(tokens):
            # remove first and last "
            return norm_string(tokens[0][1:-1])

        def unescape_multi_string(tokens):
            # remove the first and last 3 "
            return norm_string(tokens[0][3: -3])

        def convert_number(tokens):
            n = tokens[0]
            try:
                return int(n)
            except ValueError:
                return float(n)

        ParserElement.setDefaultWhitespaceChars(' \t')

        dict_expr = Forward()
        list_expr = Forward()
        assign_expr = Forward()

        true_expr = Keyword("true", caseless=True).setParseAction(replaceWith(True))
        false_expr = Keyword("false", caseless=True).setParseAction(replaceWith(False))
        null_expr = Keyword("null", caseless=True).setParseAction(replaceWith(None))
        key = QuotedString('"', escChar='\\') | Word(alphanums + '._')

        comment = (Regex('#.*[\n\r]') | Regex('//.*[\n\r]')).suppress()
        number_expr = Regex('[+-]?(\d*\.\d+|\d+(\.\d+)?)([eE]\d+)?(?=[/#,\s\]\}])').setParseAction(convert_number)
        eol = Word('\n\r').suppress()
        eol_comma = Word('\n\r,').suppress()

        # multi line string using """
        # Using fix described in http://pyparsing.wikispaces.com/share/view/3778969
        multiline_string = Regex('""".*?"""', re.DOTALL).setParseAction(unescape_multi_string)
        # single quoted line string
        singleline_string = Regex(r'\"(?:\\\"|\\\\|[^"])*\"', re.DOTALL).setParseAction(unescape_quoted_string)
        # default string that takes the rest of the line until an optional comment
        # we support .properties multiline support which is like this:
        # line1  \
        # line2 \
        # so a backslash precedes the \n
        defaultline_string = Regex(r'(\\\n|[^\[\{\n\]\}#,=])+?(?=\s*(?://|[\n#,\]\}]))', re.DOTALL).setParseAction(unescape_string)
        string_expr = multiline_string | singleline_string | defaultline_string

        value_expr = number_expr | true_expr | false_expr | null_expr | string_expr
        any_expr = comment | list_expr | value_expr | dict_expr

        # TODO: find a way to make comma optional and yet works with multilines
        list_elements = any_expr - Optional(eol_comma) - ZeroOrMore(any_expr - Optional(eol_comma))
        list_expr << ListParser(
            (Suppress('[') - Optional(eol) - Optional(list_elements) - Suppress(']'))) + Optional(
            comment | eol_comma)

        # for a dictionary : or = is optional
        # last zeroOrMore is because we can have t = {a:4} {b: 6} {c: 7} which is dictionary concatenation
        dict_expr << ConfigTreeParser(Suppress('{') - ZeroOrMore(comment | assign_expr | eol) + Suppress('}')) - ZeroOrMore(dict_expr)
        assign_dict_expr = Suppress(Optional(oneOf(['=', ':']))) + dict_expr

        # special case when we have a value assignment where the string can potentially be the remainder of the line
        assign_value_or_list_expr = Suppress(oneOf(['=', ':'])) + (list_expr | value_expr | eol_comma)
        assign_expr << Group(key + (assign_dict_expr | assign_value_or_list_expr)) + Optional(eol_comma)

        # the file can be { ... } where {} can be omitted or []
        config_expr = ZeroOrMore(comment | eol) \
            + (list_expr | dict_expr | ConfigTreeParser(ZeroOrMore(comment | assign_expr))) \
            + ZeroOrMore(comment | eol_comma)
        config = config_expr.parseString(content, parseAll=True)[0]

        # if config consists in a list
        return config if isinstance(config, ConfigTree) else list(config)


class ListParser(TokenConverter):
    """
    Parse a list [elt1, etl2, ...]
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
        res = []
        for index, token in enumerate(token_list):
            if token == '':
                # does not support a,,b
                if index < len(token_list) - 1:
                    raise ConfigException("Does not accept list with empty values {list}".format(list=repr(token_list)))
            else:
                res.append(token)

        return [res]


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
                for value in values:
                    conf_value = list(value) if isinstance(value, ParseResults) else value
                    config_tree.put(key, conf_value)

        return config_tree
