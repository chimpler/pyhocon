import itertools
from datetime import timedelta

from pyparsing import (Word, ZeroOrMore, alphanums, Or, nums, WordEnd, Combine, Literal)

period_type_map = {
    'nanoseconds': ['ns', 'nano', 'nanos', 'nanosecond', 'nanoseconds'],
    'microseconds': ['us', 'micro', 'micros', 'microsecond', 'microseconds'],
    'milliseconds': ['ms', 'milli', 'millis', 'millisecond', 'milliseconds'],
    'seconds': ['s', 'second', 'seconds'],
    'minutes': ['m', 'minute', 'minutes'],
    'hours': ['h', 'hour', 'hours'],
    'weeks': ['w', 'week', 'weeks'],
    'days': ['d', 'day', 'days'],
}

optional_period_type_map = {
    'months': ['mo', 'month', 'months'],  # 'm' from hocon spec removed. conflicts with minutes syntax.
    'years': ['y', 'year', 'years']
}

try:
    from dateutil.relativedelta import relativedelta as period_impl

    if period_impl is not None:
        period_type_map.update(optional_period_type_map)
except ImportError:
    period_impl = timedelta


def convert_period(tokens):
    period_value = int(tokens.value)
    period_identifier = tokens.unit

    period_unit = next((single_unit for single_unit, values
                        in period_type_map.items()
                        if period_identifier in values))

    return period(period_value, period_unit)


def period(period_value, period_unit):
    if period_unit == 'nanoseconds':
        period_unit = 'microseconds'
        period_value = int(period_value / 1000)

    arguments = dict(zip((period_unit,), (period_value,)))

    if period_unit == 'milliseconds':
        return timedelta(**arguments)

    return period_impl(**arguments)


def get_period_expr():
    # Flatten the list of lists with unit strings.
    period_types = list(itertools.chain(*period_type_map.values()))
    # `Or()` tries to match the longest expression if more expressions
    # are matching. We employ this to match e.g.: 'weeks' so that we
    # don't end up with 'w' and 'eeks'. Note that 'weeks' but also 'w'
    # are valid unit identifiers.
    # Allow only spaces as a valid separator between value and unit.
    # E.g. \t as a separator is invalid: '10<TAB>weeks'.
    return Combine(
            Word(nums)('value') + ZeroOrMore(Literal(" ")).suppress() + Or(period_types)('unit') + WordEnd(
        alphanums).suppress()
    ).setParseAction(convert_period)


def parse_period(content):
    return get_period_expr().parseString(content, parseAll=True)[0]
