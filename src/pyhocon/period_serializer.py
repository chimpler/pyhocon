from datetime import timedelta

try:
    from dateutil.relativedelta import relativedelta
except Exception:
    relativedelta = None


def is_timedelta_like(config):
    return isinstance(config, timedelta) or relativedelta is not None and isinstance(config, relativedelta)


def timedelta_to_hocon(config):
    """:type config: timedelta|relativedelta"""
    if relativedelta is not None and isinstance(config, relativedelta):
        if config.hours > 0:
            return str(config.hours) + ' hours'
        elif config.minutes > 0:
            return str(config.minutes) + ' minutes'

    if config.days > 0:
        return str(config.days) + ' days'
    elif config.seconds > 0:
        return str(config.seconds) + ' seconds'
    elif config.microseconds > 0:
        return str(config.microseconds) + ' microseconds'
    else:
        return '0 seconds'


def relative_delta_to_timedelta(relative_delta):
    """:type relative_delta: relativedelta"""
    return timedelta(days=relative_delta.days,
                     hours=relative_delta.hours,
                     minutes=relative_delta.minutes,
                     seconds=relative_delta.seconds,
                     microseconds=relative_delta.microseconds)


def timedelta_to_str(config):
    if relativedelta is not None and isinstance(config, relativedelta):
        time_delta = relative_delta_to_timedelta(config)
    else:
        time_delta = config
    return str(int(time_delta.total_seconds() * 1000))
