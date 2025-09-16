"""
Constants module for the amaru package.

Constants' description:

    XML: xml used in the AWS S3 service, for Goes 16 onwards.
    CHANGE_TO_AWS: date when .NCs are available in AWS S3, dates before are hosted in the NOAAH site.
    URLNOAAH: URL of the NOAAH site.
    TIME_DIFFERENCE: timedelta object representing 1 hour.

.NC asttributes:
    XMIN: Left edge.
    YMAX: Top edge.
    XRES: Horizontal pixel size.
    YRES: Vertical pixel size.
    WIDTH: length of horizontal pixels.
    HEIGHT: length of vertical pixels.
"""

__all__ = ["XMIN", "YMAX", "XRES", "YRES", "WIDTH", "HEIGHT", "YMIN", "XMAX"]


from typing import Final
from datetime import datetime, timedelta
import os

XML: Final[str] = "https://noaa-goes16.s3.amazonaws.com/"
CHANGE_TO_AWS: Final[datetime] = datetime(2017, 2, 28)
URLNOAAH: Final[str] = "https://www.ncei.noaa.gov/data/gridsat-goes/access/goes/"
TIME_DIFFERENCE = timedelta(hours=1)

XMIN: Final[float] = -85.0
YMAX: Final[float] = -9.984984984984990
XRES: Final[float] = 0.037537537537538
YRES: Final[float] = 0.037537537537538
WIDTH: Final[int] = 666
HEIGHT: Final[int] = 800
YMIN: Final[float] = YMAX - (HEIGHT * YRES)
XMAX: Final[float] = XMIN + (WIDTH * XRES)

_PATH_GOES_MONTHS: Final[str] = os.path.join("src", "amaru", "data", "goes_months.json")
_PATH_NOAAH_SATELLITES: Final[str] = os.path.join(
    "src", "amaru", "data", "noaah_satellites.json"
)
_PATH_INVALID_DATES: Final[str] = os.path.join(
    "src", "amaru", "data", "invalid_dates.json"
)
_PATH_INVALID_DATA: Final[str] = os.path.join(
    "src", "amaru", "data", "invalid_data.json"
)
