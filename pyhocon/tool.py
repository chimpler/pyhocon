import argparse
import sys
from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigTree


class HOCONConverter(object):
    @staticmethod
    def to_json(config, level=0):
        """
        Convert HOCON input into a JSON output
        :return:
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
        else:
            lines = str(config)
        return lines

    @staticmethod
    def to_yaml(config, level=0):
        """
        Convert HOCON input into a JSON output
        :return:
        """
        lines = ""
        if isinstance(config, ConfigTree):
            if len(config) > 0:
                if level > 0:
                    lines += '\n'
                bet_lines = []
                for key, item in config.items():
                    bet_lines.append('{indent}{key}: {value}'.format(
                        indent=''.rjust((level + 1) * 2, ' '),
                        key=key,
                        value=HOCONConverter.to_yaml(item, level + 1))
                    )
                lines += '\n'.join(bet_lines)
        elif isinstance(config, list):
            if len(config) == 0:
                lines += '[]'
            else:
                lines += '\n'
                bet_lines = []
                for item in config:
                    bet_lines.append('{indent}- {value}'.format(indent=''.rjust((level + 1) * 2, ' '), value=HOCONConverter.to_yaml(item, level + 1)))
                lines += '\n'.join(bet_lines)
        elif isinstance(config, str):
            # if it contains a \n then it's multiline
            lines = config.split('\n')
            if len(lines) == 1:
                lines = config
            else:
                lines = '|\n' + '\n'.join([line.rjust((level + 1) * 2, ' ') for line in lines])
        else:
            lines = str(config)
        return lines

    @staticmethod
    def to_properties(config, key_stack=[]):
        """
        Convert HOCON input into a .properties output
        :return:
        """
        def escape_value(value):
            return value.replace('=', '\\=').replace('!', '\\!').replace('#', '\\#').replace('\n', '\\\n')

        lines = []
        if isinstance(config, ConfigTree):
            for key, item in config.items():
                lines.append(HOCONConverter.to_properties(item, key_stack + [key]))
        elif isinstance(config, list):
            for index, item in enumerate(config):
                lines.append(HOCONConverter.to_properties(item, key_stack + [str(index)]))
        elif isinstance(config, str):
            lines.append('.'.join(key_stack) + ' = ' + escape_value(config))
        else:
            lines.append('.'.join(key_stack) + ' = ' + str(config))
        return '\n'.join([line for line in lines if len(line) > 0])

    @staticmethod
    def convert(format):
        content = sys.stdin.read()
        config = ConfigFactory.parse_string(content)
        if format.lower() == 'json':
            print HOCONConverter.to_json(config)
        elif format.lower() == 'properties':
            print HOCONConverter.to_properties(config)
        elif format.lower() == 'yaml':
            print HOCONConverter.to_yaml(config)
        else:
            raise Exception("Format must be 'json', 'properties' or 'yaml'")


def main():
    parser = argparse.ArgumentParser(description='pyhocon tool')
    parser.add_argument('-f', '--format', help='output format: json or properties', default='json')
    args = parser.parse_args()
    if args.format.lower() not in ['json', 'properties', 'yaml']:
        raise Exception("Format must be 'json', 'properties' or 'yaml'")
    HOCONConverter.convert(args.format)


if __name__ == '__main__':
    main()
