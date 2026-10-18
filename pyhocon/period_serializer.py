from datetime import timedelta

try:
    from dateutil.relativedelta import relativedelta
except Exception:
    relativedelta = None


def is_timedelta_like(config):
    return isinstance(config, timedelta) or relativedelta is not None and isinstance(config, relativedelta)


def timedelta_to_hocon(config):
    """:type config: timedelta|relativedelta"""
    components = [(config.days, 'days', 86400 * 1000000),
                  (config.seconds, 'seconds', 1000000),
                  (config.microseconds, 'microseconds', 1)]
    if relativedelta is not None and isinstance(config, relativedelta):
        absolute_fields = ('year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond', 'weekday')
        if config.years or config.months or config.leapdays or any(getattr(config, field) is not None for field in absolute_fields):
            components = []
        else:
            components[1:1] = [(config.hours, 'hours', 3600 * 1000000),
                               (config.minutes, 'minutes', 60 * 1000000)]

    # Keep every component of a fixed duration, using integer arithmetic to
    # preserve microseconds even for large values. Leave other period behavior
    # and the existing single-component representations unchanged.
    nonzero_components = [(value, unit, scale) for value, unit, scale in components if value]
    if len(nonzero_components) > 1 and all(isinstance(value, int) and value >= 0 for value, _, _ in components):
        total_microseconds = sum(value * scale for value, _, scale in components)
        _, unit, scale = nonzero_components[-1]
        return str(total_microseconds // scale) + ' ' + unit

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
