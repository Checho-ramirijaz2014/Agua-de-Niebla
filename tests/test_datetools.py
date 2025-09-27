import pytest
from datetime import datetime, timedelta
from amaru.datetools import timerange, get_first_day

def create_generator_and_date_list(start: datetime, end: datetime):

    diff_time = int((end - start).total_seconds()) // 3600
    date_list = [start + timedelta(hours=hour) for hour in range(diff_time)]

    generator_test = timerange(start, end)
    return generator_test, date_list


test_start_datetime_end_datetime = create_generator_and_date_list(datetime(2017, 1, 1), datetime(2018, 1, 1))
test_same_days_different_hour = create_generator_and_date_list(datetime(2017, 1, 1, 2), datetime(2017, 1, 1, 23))


@pytest.mark.parametrize("generator, expected_values", [
    test_start_datetime_end_datetime,
    test_same_days_different_hour                    
])
def test_timerange(generator: timerange, expected_values):
    index_timerange = 0
    for actual_value in generator:
        assert index_timerange + 1 <= len(expected_values)
        assert expected_values[index_timerange] == actual_value
        index_timerange += 1

    assert index_timerange == len(expected_values)


@pytest.mark.parametrize("day, expected_next_month_day", [

])
def test_get_first_day(day: datetime, expected_next_month_day):
    pass
