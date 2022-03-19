from datetime import timedelta

import pytest

from pyhocon.period_parser import parse_period
from pyhocon.period_serializer import timedelta_to_hocon

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
except Exception:
    pass


def test_format_time_delta():
    for time_delta, expected_result in ((timedelta(days=0), '0 seconds'),
                                        (timedelta(days=5), '5 days'),
                                        (timedelta(seconds=51), '51 seconds'),
                                        (timedelta(microseconds=786), '786 microseconds')):
        assert expected_result == timedelta_to_hocon(time_delta)


def test_format_relativedelta():
    try:
        from dateutil.relativedelta import relativedelta
    except Exception:
        return

    for time_delta, expected_result in ((relativedelta(seconds=0), '0 seconds'),
                                        (relativedelta(hours=0), '0 seconds'),
                                        (relativedelta(days=5), '5 days'),
                                        (relativedelta(weeks=3), '21 days'),
                                        (relativedelta(hours=2), '2 hours'),
                                        (relativedelta(minutes=43), '43 minutes'),):
        assert expected_result == timedelta_to_hocon(time_delta)
