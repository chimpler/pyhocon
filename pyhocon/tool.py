import argparse
import logging
import sys
from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigTree

try:
    basestring
except NameError:
    basestring = str


LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'


class HOCONConverter(object):

    @staticmethod
    def to_json(config, indent=2, level=0):
        """Convert HOCON input into a JSON output

        :return: JSON string representation
        :type return: basestring
        """
        lines = ""
        if isinstance(config, ConfigTree):
            if len(config) == 0:
                lines += '{}'
            else:
                lines += '{\n'
                bet_lines = []
                for key, item in config.items():
                    bet_lines.append('{indent}"{key}": {value}'.format(
                        indent=''.rjust((level + 1) * indent, ' '),
                        key=key.strip('"'),  # for dotted keys enclosed with "" to not be interpreted as nested key
                        value=HOCONConverter.to_json(item, indent, level + 1))
                    )
                lines += ',\n'.join(bet_lines)
                lines += '\n{indent}}}'.format(indent=''.rjust(level * indent, ' '))
        elif isinstance(config, list):
            if len(config) == 0:
                lines += '[]'
            else:
                lines += '[\n'
                bet_lines = []
                for item in config:
                    bet_lines.append('{indent}{value}'.format(
                        indent=''.rjust((level + 1) * indent, ' '),
                        value=HOCONConverter.to_json(item, indent, level + 1))
                    )
                lines += ',\n'.join(bet_lines)
                lines += '\n{indent}]'.format(indent=''.rjust(level * indent, ' '))
        elif isinstance(config, basestring):
            lines = '"{value}"'.format(value=config.replace('\n', '\\n').replace('"', '\\"'))
        elif config is None:
            lines = 'null'
        elif config is True:
            lines = 'true'
        elif config is False:
            lines = 'false'
        else:
            lines = str(config)
        return lines

    @staticmethod
    def to_hocon(config, indent=2, level=0):
        """Convert HOCON input into a HOCON output

        :return: JSON string representation
        :type return: basestring
        """
        lines = ""
        if isinstance(config, ConfigTree):
            if len(config) == 0:
                lines += '{}'
            else:
                if level > 0:  # don't display { at root level
                    lines += '{\n'
                bet_lines = []
                for key, item in config.items():
                    bet_lines.append('{indent}{key}{assign_sign} {value}'.format(
                        indent=''.rjust(level * indent, ' '),
                        key=key,
                        assign_sign='' if isinstance(item, dict) else ' =',
                        value=HOCONConverter.to_hocon(item, indent, level + 1))
                    )
                lines += '\n'.join(bet_lines)

                if level > 0:  # don't display { at root level
                    lines += '\n{indent}}}'.format(indent=''.rjust((level - 1) * indent, ' '))
        elif isinstance(config, list):
            if len(config) == 0:
                lines += '[]'
            else:
                lines += '[\n'
                bet_lines = []
                for item in config:
                    bet_lines.append('{indent}{value}'.format(indent=''.rjust(level * indent, ' '), value=HOCONConverter.to_hocon(item, indent, level + 1)))
                lines += '\n'.join(bet_lines)
                lines += '\n{indent}]'.format(indent=''.rjust((level - 1) * indent, ' '))
        elif isinstance(config, basestring):
            if '\n' in config:
                lines = '"""{value}"""'.format(value=config)  # multilines
            else:
                lines = '"{value}"'.format(value=config.replace('\n', '\\n').replace('"', '\\"'))
        elif config is None:
            lines = 'null'
        elif config is True:
            lines = 'true'
        elif config is False:
            lines = 'false'
        else:
            lines = str(config)
        return lines

    @staticmethod
    def to_yaml(config, indent=2, level=0):
        """Convert HOCON input into a YAML output

        :return: YAML string representation
        :type return: basestring
        """
        lines = ""
        if isinstance(config, ConfigTree):
            if len(config) > 0:
                if level > 0:
                    lines += '\n'
                bet_lines = []
                for key, item in config.items():
                    bet_lines.append('{indent}{key}: {value}'.format(
                        indent=''.rjust(level * indent, ' '),
                        key=key.strip('"'),  # for dotted keys enclosed with "" to not be interpreted as nested key,
                        value=HOCONConverter.to_yaml(item, indent, level + 1))
                    )
                lines += '\n'.join(bet_lines)
        elif isinstance(config, list):
            config_list = [line for line in config if line is not None]
            if len(config_list) == 0:
                lines += '[]'
            else:
                lines += '\n'
                bet_lines = []
                for item in config_list:
                    bet_lines.append('{indent}- {value}'.format(indent=''.rjust(level * indent, ' '), value=HOCONConverter.to_yaml(item, indent, level + 1)))
                lines += '\n'.join(bet_lines)
        elif isinstance(config, basestring):
            # if it contains a \n then it's multiline
            lines = config.split('\n')
            if len(lines) == 1:
                lines = config
            else:
                lines = '|\n' + '\n'.join([line.rjust(level * indent, ' ') for line in lines])
        elif config is True:
            lines = 'true'
        elif config is False:
            lines = 'false'
        else:
            lines = str(config)
        return lines

    @staticmethod
    def to_properties(config, indent=2, key_stack=[]):
        """Convert HOCON input into a .properties output

        :return: .properties string representation
        :type return: basestring
        :return:
        """
        def escape_value(value):
            return value.replace('=', '\\=').replace('!', '\\!').replace('#', '\\#').replace('\n', '\\\n')

        stripped_key_stack = [key.strip('"') for key in key_stack]
        lines = []
        if isinstance(config, ConfigTree):
            for key, item in config.items():
                if item is not None:
                    lines.append(HOCONConverter.to_properties(item, indent, stripped_key_stack + [key]))
        elif isinstance(config, list):
            for index, item in enumerate(config):
                if item is not None:
                    lines.append(HOCONConverter.to_properties(item, indent, stripped_key_stack + [str(index)]))
        elif isinstance(config, basestring):
            lines.append('.'.join(stripped_key_stack) + ' = ' + escape_value(config))
        elif config is True:
            lines.append('.'.join(stripped_key_stack) + ' = true')
        elif config is False:
            lines.append('.'.join(stripped_key_stack) + ' = false')
        else:
            lines.append('.'.join(stripped_key_stack) + ' = ' + str(config))
        return '\n'.join([line for line in lines if len(line) > 0])

    @staticmethod
    def convert(config, output_format='json', indent=2):
        converters = {
            'json': HOCONConverter.to_json,
            'properties': HOCONConverter.to_properties,
            'yaml': HOCONConverter.to_yaml,
            'hocon': HOCONConverter.to_hocon,
        }

        if output_format in converters:
            return converters[output_format](config, indent)
        else:
            raise Exception("Invalid format '{format}'. Format must be 'json', 'properties', 'yaml' or 'hocon'".format(format=output_format))

    @staticmethod
    def convert_from_file(input_file=None, output_file=None, output_format='json', indent=2):
        """Convert to json, properties or yaml

        :param input_file: input file, if not specified stdin
        :param output_file: output file, if not specified stdout
        :param output_format: json, properties or yaml
        :return: json, properties or yaml string representation
        """

        if input_file is None:
            content = sys.stdin.read()
            config = ConfigFactory.parse_string(content)
        else:
            config = ConfigFactory.parse_file(input_file)

        res = HOCONConverter.convert(config, output_format, indent)
        if output_file is None:
            print(res)
        else:
            with open(output_file, "w") as fd:
                fd.write(res)


def main():  # pragma: no cover
    parser = argparse.ArgumentParser(description='pyhocon tool')
    parser.add_argument('-i', '--input', help='input file')
    parser.add_argument('-o', '--output', help='output file')
    parser.add_argument('-f', '--format', help='output format: json, properties, yaml or hocon', default='json')
    parser.add_argument('-n', '--indent', help='indentation step (default is 2)', default=2, type=int)
    parser.add_argument('-v', '--verbosity', action='count', default=0, help='increase output verbosity')
    args = parser.parse_args()

    # Python 2.6 support
    def null_handler():
        return logging.NullHandler() if hasattr(logging, 'NullHandler') else logging.FileHandler('/dev/null')
    logger = logging.getLogger()
    log_handler = logging.StreamHandler() if args.verbosity > 0 else null_handler()
    log_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(log_handler)
    if args.verbosity == 1:
        logger.setLevel(logging.ERROR)
    elif args.verbosity == 2:
        logger.setLevel(logging.INFO)
    elif args.verbosity >= 3:
        logger.setLevel(logging.DEBUG)

    HOCONConverter.convert_from_file(args.input, args.output, args.format.lower(), args.indent)


if __name__ == '__main__':  # pragma: no cover
    main()
