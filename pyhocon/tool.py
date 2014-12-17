import argparse
import sys
from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigTree


class HOCONConverter(object):
    @staticmethod
    def to_json(config, level=0):
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
                        indent=''.rjust((level + 1) * 2, ' '),
                        key=key,
                        value=HOCONConverter.to_json(item, level + 1))
                    )
                lines += ',\n'.join(bet_lines)
                lines += '\n{indent}}}'.format(indent=''.rjust(level * 2, ' '))
        elif isinstance(config, list):
            if len(config) == 0:
                lines += '[]'
            else:
                lines += '[\n'
                bet_lines = []
                for item in config:
                    bet_lines.append('{indent}{value}'.format(indent=''.rjust((level + 1) * 2, ' '), value=HOCONConverter.to_json(item, level + 1)))
                lines += ',\n'.join(bet_lines)
                lines += '\n{indent}]'.format(indent=''.rjust(level * 2, ' '))
        elif isinstance(config, str):
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
    def to_yaml(config, level=0):
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
                        indent=''.rjust(level * 2, ' '),
                        key=key,
                        value=HOCONConverter.to_yaml(item, level + 1))
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
                    bet_lines.append('{indent}- {value}'.format(indent=''.rjust(level * 2, ' '), value=HOCONConverter.to_yaml(item, level + 1)))
                lines += '\n'.join(bet_lines)
        elif isinstance(config, str):
            # if it contains a \n then it's multiline
            lines = config.split('\n')
            if len(lines) == 1:
                lines = config
            else:
                lines = '|\n' + '\n'.join([line.rjust(level * 2, ' ') for line in lines])
        elif config is True:
            lines = 'true'
        elif config is False:
            lines = 'false'
        else:
            lines = str(config)
        return lines

    @staticmethod
    def to_properties(config, key_stack=[]):
        """Convert HOCON input into a .properties output

        :return: .properties string representation
        :type return: basestring
        :return:
        """
        def escape_value(value):
            return value.replace('=', '\\=').replace('!', '\\!').replace('#', '\\#').replace('\n', '\\\n')

        lines = []
        if isinstance(config, ConfigTree):
            for key, item in config.items():
                if item is not None:
                    lines.append(HOCONConverter.to_properties(item, key_stack + [key]))
        elif isinstance(config, list):
            for index, item in enumerate(config):
                if item is not None:
                    lines.append(HOCONConverter.to_properties(item, key_stack + [str(index)]))
        elif isinstance(config, str):
            lines.append('.'.join(key_stack) + ' = ' + escape_value(config))
        elif config is True:
            lines.append('.'.join(key_stack) + ' = true')
        elif config is False:
            lines.append('.'.join(key_stack) + ' = false')
        else:
            lines.append('.'.join(key_stack) + ' = ' + str(config))
        return '\n'.join([line for line in lines if len(line) > 0])

    @staticmethod
    def convert(input_file=None, output_file=None, format='json'):
        """Convert to json, properties or yaml

        :param format: json, properties or yaml
        :type format: basestring
        :return: json, properties or yaml string representation
        """

        if input_file is None:
            content = sys.stdin.read()
            config = ConfigFactory.parse_string(content)
        else:
            config = ConfigFactory.parse_file(input_file)

        if format.lower() == 'json':
            res = HOCONConverter.to_json(config)
        elif format.lower() == 'properties':
            res = HOCONConverter.to_properties(config)
        elif format.lower() == 'yaml':
            res = HOCONConverter.to_yaml(config)
        else:
            raise Exception("Format must be 'json', 'properties' or 'yaml'")

        if output_file is None:
            print res
        else:
            with open(output_file, "w") as fd:
                fd.write(res)


def main():
    parser = argparse.ArgumentParser(description='pyhocon tool')
    parser.add_argument('-i', '--input', help='input file')
    parser.add_argument('-o', '--output', help='output file')
    parser.add_argument('-f', '--format', help='output format: json, properties or yaml', default='json')
    args = parser.parse_args()
    if args.format.lower() not in ['json', 'properties', 'yaml']:
        raise Exception("Format must be 'json', 'properties' or 'yaml'")
    HOCONConverter.convert(args.input, args.output, args.format)


if __name__ == '__main__':
    main()
