from datetime import timedelta, datetime
from typing import Generator
from .constants import TIME_DIFFERENCE
import time
from functools import wraps


def timerange(start: datetime, end: datetime) -> Generator[datetime, None, None]:
    """
    Defines a generator that creates datetime objects for
    every hour. includes the start datetime but not the end datetime.

    Parameters
    ----------
    start : datetime
        start of the generator. included in the generator.
    end: datetime
        end of the generator. last hour before this included.

    Examples
    --------
    1. Generate all hours on January 1.

    >>> timerange(datetime(2017, 1, 1), datetime(2017, 2, 1))

    2. Generate all hours on January 1 from 00:00 AM to 6 AM.

    >>> datetime_range = timerange(datetime(2017, 1, 1), datetime(2017, 1, 1, 7))
    >>> for datetime_ in datetime_range:
    ...     print(datetime_)
    ...
    datetime.datetime(2017, 1, 1, 0, 0)
    datetime.datetime(2017, 1, 1, 1, 0)
    datetime.datetime(2017, 1, 1, 2, 0)
    datetime.datetime(2017, 1, 1, 3, 0)
    datetime.datetime(2017, 1, 1, 4, 0)
    datetime.datetime(2017, 1, 1, 5, 0)
    datetime.datetime(2017, 1, 1, 6, 0)
    # Note it doesn't include 7 AM on the dates.
    """

    curr = start
    while curr < end:
        yield curr
        curr += TIME_DIFFERENCE


def _retry(max_retries: int, delay: int = 1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Error occurred: {e}. Retrying...")
                    time.sleep(delay)
            raise Exception(f"Maximun retires exceed. {func.__name__} failed")

        return wrapper

    return decorator


def check_goes_dates_are_there(start: datetime, end: datetime, images) -> list:
    gen_timerange = timerange(start, end)
    dates_not_available = []
    for datetime_ in gen_timerange:
        fecha = (
            f"{datetime_.year}.{datetime_.month:02}.{datetime_.day:02}."
            + f"{datetime_.hour:02}00"
        )
        containts = any(fecha in image for image in images)
        if not containts:
            dates_not_available.append(fecha)
    return dates_not_available


def get_first_day(day: datetime) -> datetime:
    """get the first day of the next month"""
    return (day.replace(day=1) + timedelta(days=32)).replace(day=1)
