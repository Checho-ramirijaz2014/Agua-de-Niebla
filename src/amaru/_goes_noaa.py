import multiprocessing as mp
import os
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import warnings
from pathlib import Path
from typing import Any, Generator
from itertools import batched
from functools import singledispatchmethod
from .constants import (
    URLNOAAH,
    _PATH_INVALID_DATA,
    _PATH_INVALID_DATES,
    _PATH_NOAAH_SATELLITES,
)
from datetime import datetime
from rich.progress import (
    Progress,
    Console,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
    TransferSpeedColumn,
)


def sort_(list_: list) -> list:
    return sorted(list_, key=lambda x: int(x[-2:]), reverse=True)


def format_noaah(format: datetime) -> str:
    return format.strftime("%Y.%m.%d.%H00")


with open(_PATH_INVALID_DATES, "r") as indatesfile, open(
    _PATH_INVALID_DATA, "r"
) as indatafile, open(_PATH_NOAAH_SATELLITES, "r") as satellitesfile:
    _invalid_dates = json.load(indatesfile)
    _invalid_data = json.load(indatafile)
    _noaah_satellites = json.load(satellitesfile)


class _GoesNOAA:
    """Class designed to download images from the noaa page, previous releases from 1994 to 2017"""

    __slots__ = (
        "path",
        "console",
        "datelist",
        "cpu",
        "satellites",
        "skip",
        "datetime_",
        "path_",
    )

    def __init__(
        self,
        datelist: Generator[datetime],
        path: str,
        console: Console,
        cpu: int,
        satellite: list[str] | dict[str, str],
        skip,
    ):
        self.datelist = datelist
        self.path = path
        self.console = console
        self.cpu = cpu
        self.satellites = self.satellite_selection(satellite)
        self.skip = skip
        if self.cpu > 1:
            self.datelist = batched(self.datelist, self.cpu)

    def _prepare_download(self) -> None:
        for datetime_ in self.datelist:
            self.datetime_ = datetime_
            self.path_ = Path(
                self.path
                / "NOAAH"
                / str(datetime_.year)
                / datetime_.strftime("%b")
                / str(datetime_.day)
            )

            self.path_.mkdir(parents=True, exist_ok=True)
            self._descargar()

    def _descargar(self) -> None:
        """Gestiona la descarga de una fecha en especifico"""

        if self.cpu > 1:
            with mp.Pool(self.cpu) as pool:
                pool.starmap(
                    self._descarga,
                    [(self.path, imagen, self.satellites) for imagen in self.datetime_],
                )
        else:
            self._descarga(self.path_, self.datetime_, self.satellites)

    def __log(self, string):
        self.console.log(string)

    @singledispatchmethod
    def satellite_selection(self, arg: Any):
        raise TypeError("Only instances of list or dict")

    @satellite_selection.register
    def _(self, arg: dict):
        return arg

    @satellite_selection.register
    def _(self, arg: list):
        return arg

    @staticmethod
    def _descarga(
        path: str, datetime_: datetime, satellites: list[str] | None, skip: bool = False
    ) -> None:

        # defaul satellites if not selected
        if satellites is None:
            satellites = sort_(
                _noaah_satellites[str(datetime_.year)][str(datetime_.month)]
            )

        date_f = format_noaah(datetime_)

        for satellite in satellites:
            if (
                date_f
                not in _invalid_dates[str(datetime_.year)][str(datetime_.month)][
                    satellite
                ]
            ):

                url = (
                    URLNOAAH
                    + datetime_.strftime("%Y/%m/")
                    + "GridSat-GOES."
                    + satellite
                    + datetime_.strftime(".%Y.%m.%d.%H00")
                    + ".v01.nc"
                )

                response = requests.get(url, stream=True)
                total_length = int(response.headers.get("content-length", 0))

                namefile = os.path.join(path, url.split("/")[-1])

                progress = Progress(
                    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
                    BarColumn(bar_width=None),
                    "•",
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    "•",
                    TransferSpeedColumn(),  # Show download process time
                    "•",
                    TimeRemainingColumn(),  # Show remaining time left
                    "•",
                    TimeElapsedColumn(),  # Show time since starting download
                )

                with open(namefile, "wb") as file, progress:
                    task_descarga = progress.add_task(
                        "[cyan]Download...", total=total_length, filename=url
                    )
                    for chunk in response.iter_content(chunk_size=4096):
                        file.write(chunk)
                        progress.update(task_descarga, advance=len(chunk), refresh=True)
                break
        else:
            warnings.warn(f"date {date_f} not available in any satellite: {satellites}")
