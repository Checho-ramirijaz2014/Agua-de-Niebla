from datetime import timedelta, datetime
from typing import Generator
from bs4 import BeautifulSoup

TIME_DIFFERENCE = timedelta(hours=1)


def timerange(start: datetime, end: datetime) -> Generator:
    """Defines a generator that creates datetime objects for
    every hour"""
    curr = start
    while curr < end:
        yield curr
        curr += TIME_DIFFERENCE


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


with open("noaa_html_de_prueba.html", "rt") as html:
    content = html.read()

# soup = BeautifulSoup(content, "")
# soup.findall("a") #find("body").find("table").find("tr")
# list_ = [row.text for row in soup.find_all("a")]
# list_15 = [s for s in list_ if "goes15" in s]
# list_13 = [s for s in list_ if "goes13" in s]
# print(check_goes_dates_are_there(datetime(2015, 1, 1), datetime(2015, 2, 1), list_15))
