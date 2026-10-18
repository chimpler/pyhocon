from datetime import timedelta

import pytest

from pyhocon.period_parser import parse_period
from pyhocon.period_serializer import timedelta_to_hocon

try:
    from dateutil.relativedelta import relativedelta as period
except ImportError:
    period = timedelta


@pytest.mark.parametrize('data_set', [
    ('1 minutes', period(minutes=1)),
    ('1minutes', period(minutes=1)),
    ('2 minute', period(minutes=2)),
    ('3 m', period(minutes=3)),
    ('3m', period(minutes=3)),

    ('4 seconds', period(seconds=4)),
    ('5 second', period(seconds=5)),
    ('6 s', period(seconds=6)),

    ('7 hours', period(hours=7)),
    ('8 hour', period(hours=8)),
    ('9 h', period(hours=9)),

    ('10 weeks', period(weeks=10)),
    ('11 week', period(weeks=11)),
    ('12 w', period(weeks=12)),

    ('10 days', period(days=10)),
    ('11 day', period(days=11)),
    ('12 d', period(days=12)),

    ('110 microseconds', period(microseconds=110)),
    ('111 microsecond', period(microseconds=111)),
    ('112 micros', period(microseconds=112)),
    ('113 micro', period(microseconds=113)),
    ('114 us', period(microseconds=114)),

    ('110 milliseconds', timedelta(milliseconds=110)),
    ('111 millisecond', timedelta(milliseconds=111)),
    ('112 millis', timedelta(milliseconds=112)),
    ('113 milli', timedelta(milliseconds=113)),
    ('114 ms', timedelta(milliseconds=114)),

    ('110 nanoseconds', period(microseconds=0)),
    ('11000 nanoseconds', period(microseconds=11)),
    ('1110000 nanosecond', period(microseconds=1110)),
    ('1120000 nanos', period(microseconds=1120)),
    ('1130000 nano', period(microseconds=1130)),
    ('1140000 ns', period(microseconds=1140)),
])
def test_parse_string_with_duration(data_set):
    config = parse_period(data_set[0])

    assert config == data_set[1]


try:
    from dateutil.relativedelta import relativedelta

    @pytest.mark.parametrize('data_set', [
        ('1 months', relativedelta(months=1)),
        ('1months', relativedelta(months=1)),
        ('2 month', relativedelta(months=2)),
        ('3 mo', relativedelta(months=3)),
        ('3mo', relativedelta(months=3)),

        ('1 years', relativedelta(years=1)),
        ('1years', relativedelta(years=1)),
        ('2 year', relativedelta(years=2)),
        ('3 y', relativedelta(years=3)),
        ('3y', relativedelta(years=3)),

    ])
    def test_parse_string_with_duration_optional_units(data_set):
        parsed = parse_period(data_set[0])

        assert parsed == data_set[1]

    def test_format_relativedelta():

        for time_delta, expected_result in ((relativedelta(seconds=0), '0 seconds'),
                                            (relativedelta(hours=0), '0 seconds'),
                                            (relativedelta(days=5), '5 days'),
                                            (relativedelta(weeks=3), '21 days'),
                                            (relativedelta(hours=2), '2 hours'),
                                            (relativedelta(minutes=43), '43 minutes'),):
            assert expected_result == timedelta_to_hocon(time_delta)
except ImportError:
    pass


def test_format_time_delta():
    for time_delta, expected_result in ((timedelta(days=0), '0 seconds'),
                                        (timedelta(days=5), '5 days'),
                                        (timedelta(seconds=51), '51 seconds'),
                                        (timedelta(microseconds=786), '786 microseconds')):
        assert expected_result == timedelta_to_hocon(time_delta)


@pytest.mark.parametrize('time_delta, expected_result', [
    (timedelta(days=1, seconds=1), '86401 seconds'),
    (timedelta(seconds=1, microseconds=500000), '1500000 microseconds'),
    (timedelta(days=1, seconds=1, microseconds=1), '86401000001 microseconds'),
    (timedelta(days=100000, microseconds=1), '8640000000000001 microseconds'),
])
def test_format_time_delta_multiple_components(time_delta, expected_result):
    assert timedelta_to_hocon(time_delta) == expected_result


@pytest.mark.parametrize('fields, expected_result', [
    ({'minutes': 1, 'seconds': 30}, '90 seconds'),
    ({'hours': 1, 'minutes': 30}, '90 minutes'),
    ({'days': 1, 'hours': 1}, '25 hours'),
    ({'days': 1, 'hours': 2, 'minutes': 3, 'seconds': 4, 'microseconds': 5}, '93784000005 microseconds'),
    ({'days': 100000, 'microseconds': 1}, '8640000000000001 microseconds'),
])
def test_format_relativedelta_multiple_components(fields, expected_result):
    relativedelta = pytest.importorskip('dateutil.relativedelta').relativedelta
    assert timedelta_to_hocon(relativedelta(**fields)) == expected_result


@pytest.mark.parametrize('time_delta, expected_result', [
    (timedelta(seconds=-90), '86310 seconds'),
    (timedelta(seconds=-1, microseconds=-1), '86398 seconds'),
])
def test_format_negative_time_delta_unchanged(time_delta, expected_result):
    assert timedelta_to_hocon(time_delta) == expected_result


@pytest.mark.parametrize('fields, expected_result', [
    ({'years': 1, 'hours': 1, 'minutes': 30}, '1 hours'),
    ({'months': 1, 'hours': 1, 'minutes': 30}, '1 hours'),
    ({'leapdays': 1, 'days': 1, 'seconds': 1}, '1 days'),
    ({'day': 1, 'hours': 1, 'minutes': 30}, '1 hours'),
    ({'days': -1, 'hours': 1, 'minutes': 30}, '1 hours'),
    ({'hours': 1, 'minutes': -30}, '1 hours'),
    ({'days': 1.5, 'seconds': 1}, '1.5 days'),
])
def test_format_other_relativedelta_unchanged(fields, expected_result):
    relativedelta = pytest.importorskip('dateutil.relativedelta').relativedelta
    assert timedelta_to_hocon(relativedelta(**fields)) == expected_result
