import argparse
import logging

from pyhocon.converter import HOCONConverter

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'


def main():  # pragma: no cover
    parser = argparse.ArgumentParser(description='pyhocon tool')
    parser.add_argument('-i', '--input', help='input file')
    parser.add_argument('-o', '--output', help='output file')
    parser.add_argument('-c', '--compact', action='store_true', default=False, help='compact format')
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
    HOCONConverter.convert_from_file(args.input, args.output, args.format.lower(), args.indent, args.compact)


if __name__ == '__main__':  # pragma: no cover
    main()
