from .constants import (
    URLNOAAH,
    _PATH_GOES_MONTHS,
    _PATH_NOAAH_SATELLITES,
    _PATH_INVALID_DATES,
    _PATH_INVALID_DATA,
)
from .datetools import timerange, get_first_day
from bs4 import BeautifulSoup, Tag
import requests
from datetime import datetime
import json


__all__ = ("update",)


def update(
    update_noaah=False,
    update_noah_satellite=False,
    update_invalid_dates=False,
    update_data_not_available=False,
    all=False,
) -> None:

    if update_noaah or all:
        _get_months_for_all_years()
    if update_noah_satellite or all:
        _get_satellites_for_each_month()
    if update_invalid_dates or all:
        _get_invalid_dates()
    if update_data_not_available or all:
        _get_data_not_available()


def _clean_numbers(year: Tag) -> int | None:
    """
    extract only the numbers from str, otherwise return None.
    """
    year_text = year.text
    year_num = "".join(char for char in year_text if char.isdigit())

    if not year_num:
        return
    else:
        return int(year_num)


def _get_years() -> list[int]:
    """
    get all years from NOAAH site.
    """
    content = requests.get(URLNOAAH)
    soup = BeautifulSoup(content.text, "html.parser")
    # removes all non alphanumeric characters
    clean_list = map(_clean_numbers, soup.find_all("a"))
    # remove all None from previous function
    return list(filter(lambda x: x is not None, clean_list))


def _get_months_for_all_years() -> list[int]:
    noaah_satellite = {}
    years = _get_years()
    noaah_satellite.update({year: [] for year in years})
    for year in years:
        print(f"Getting months of year {year}")
        url = f"{URLNOAAH}{year}/"
        content = requests.get(url)
        soup = BeautifulSoup(content.text, "html.parser")

        # removes all non alphanumeric characters
        clean_list = map(_clean_numbers, soup.find_all("a"))
        # remove all None from previous function
        months = list(filter(lambda x: x is not None, clean_list))
        noaah_satellite[year] = months

    with open(_PATH_GOES_MONTHS, "w") as file:
        json.dump(noaah_satellite, file)


def _get_satellites(year: int, month: int) -> list[str]:
    content = requests.get(f"{URLNOAAH}{year}/{month:02}/")
    soup = BeautifulSoup(content.text, "html.parser")

    # removes all entries that don't have at least 1 number in it
    full_entries = [
        row.text
        for row in soup.find_all("a")
        if any(char.isdigit() for char in row.text)
    ]
    # get only the satellite data
    goes_entries = [row.split(".")[1] for row in full_entries]
    return list(set(goes_entries))


def _get_satellites_for_each_month():
    with open(_PATH_GOES_MONTHS, "r") as file:
        goes_months = json.load(file)

    noaah_satellites = {}
    for year, months in goes_months.items():
        print(f"getting satellites of year {year}")
        noaah_satellites[year] = {}
        for month in months:
            print(f"checking month: {month}")
            satellites = _get_satellites(year, month)
            noaah_satellites[year].update({month: satellites})

    with open(_PATH_NOAAH_SATELLITES, "w") as file:
        json.dump(noaah_satellites, file, indent=2)


def _get_invalid_dates():
    with open(_PATH_NOAAH_SATELLITES, "r") as file:
        noaah_satellites = json.load(file)

    invalid_dates = {}

    for year, months_dict in noaah_satellites.items():
        year = int(year)
        print(f"getting invalid dates of year {year}...")
        invalid_dates[year] = {}
        for month, satellites in months_dict.items():
            month = int(month)
            print(f"Checkin month: {month}...")
            content = requests.get(f"{URLNOAAH}{year}/{month:02}/")
            soup = BeautifulSoup(content.text, "html.parser")
            datelist = [row.text for row in soup.find_all("a")]
            invalid_dates[year][month] = {}
            for satellite in satellites:
                satellite_list = [date_ for date_ in datelist if satellite in date_]
                start = datetime(year, month, 1)
                end = get_first_day(start)
                invalid_dates_month = check_goes_dates_are_there(
                    start, end, satellite_list
                )
                invalid_dates[year][month].update({satellite: invalid_dates_month})

    with open(_PATH_INVALID_DATES, "w") as file:
        json.dump(invalid_dates, file)


def check_goes_dates_are_there(start: datetime, end: datetime, images) -> list[str]:
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


def _get_data_not_available():
    with open(_PATH_INVALID_DATES, "r") as file:
        invalid_dates = json.load(file)

    invalid_data = {}
    for year, month_data in invalid_dates.items():
        print(f"year: {year}")
        invalid_data[year] = {}
        for month, satellites in month_data.items():
            print(f"checking invalid data for month {month}")
            satellites_ = [set(id_) for id_ in satellites.values()]
            intersection_invalid_data = list(set.intersection(*satellites_))
            if not intersection_invalid_data:
                print(f"at least a satellite has data for month: {month}, year: {year}")
            else:
                print(f"Missing data: {len(intersection_invalid_data)}")
                invalid_data[year][month] = intersection_invalid_data

    with open(_PATH_INVALID_DATA, "w") as file:
        json.dump(invalid_data, file)
