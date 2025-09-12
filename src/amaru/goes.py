from datetime import datetime
from pathlib import Path
import requests
from rich.console import Console
import os
from reprlib import recursive_repr
from ._goes_r import _GoesAWS
from ._goes_noaa import _GoesNOAA
import warnings
from .datetools import timerange
from typing import Generator
from .constants import CHANGE_TO_AWS


class Goes:
    """
    Class for Interacting with the download process, using date and the metadata.

    Depending of the dates provided, it will download Netcdf files from either NOAAH or
    AWS. The satellites products used can be also specified.

    Parameters
    ----------

    inicio: datetime. A datetime object representing the start time.
    fin: datetime. Same as in inicio but representing the end time.
    path:

    """

    def __init__(
        self,
        inicio: datetime,
        fin: datetime,
        product: str=None,
        satellite: list[str] | dict[str, str] = None,
        path: str | None = Path().home() / "goes_downloaded",
        cpu=os.cpu_count(),
        skip_invalid_data: bool = False
    ):
        self._inicio = inicio
        self._fin = fin
        self._path = Path(path)
        self._console = Console()
        if inicio == fin:
            raise RuntimeError("No Data range, select different datetimes")
        self._datelist = timerange(self._inicio, self._fin)
        self._cpu = cpu
        self._product = product
        self.satellite = satellite
        self.skip = skip_invalid_data

    # Hacer que la clase solo sea de lectura

    @property
    def inicio(self):
        """fecha de inicio de la descarga"""
        return self._inicio

    @property
    def fin(self):
        """fecha de fin de la descarga"""
        return self._fin

    @property
    def path(self):
        """path donde se guadaran las imagenes"""
        return self._path

    @property
    def console(self):
        """consola que muestra los procesos"""
        return self._console

    @property
    def datelist(self):
        """tupla de fechas, incluye horas del inicio y del fin,
        si es que el objeto es datetime"""
        return self._datelist

    @property
    def cpu(self):
        """Numero de cpus que se utilizaran para la descarga.
        Por defecto es el numero de cpus disponibles en el equipo"""
        return self._cpu

    @property
    def product(self):
        return self._product

    def check_noaa(self):
        """checks connection to goes noaa"""
        try:
            response = requests.get(
                "https://www.ncei.noaa.gov/data/gridsat-goes/access/goes/"
            )
            if response.status_code == 200:
                self.__log("conection to NOAA available")
            else:
                raise requests.exceptions.HTTPError
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
            warnings.warn("Conection not available to NOAA")

    def check_aws(self):
        """checks connection to Goes AWS"""
        try:
            response = requests.get("https://noaa-goes16.s3.amazonaws.com/")
            if response.status_code == 200:
                self.__log("Conection to AWS available")
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
            warnings.warn("Conection not available to AWS")

    def descargar(self) -> None:

        if self.inicio < CHANGE_TO_AWS and self.fin < CHANGE_TO_AWS:
            # Corresponde a las imagenes del sitio de noaah
            noaah = _GoesNOAA(
                self.datelist, self.path, self.console, self.cpu, self.satellite, self.skip
            )
            noaah._prepare_download()
            del noaah

        elif CHANGE_TO_AWS <= self.inicio and CHANGE_TO_AWS < self.fin:
            # Imagenes de AWS
            aws = _GoesAWS(
                self.datelist, self.path, self.console, self.cpu, self.product
            )
            aws._prepare_download()
            del aws

        elif self.inicio < CHANGE_TO_AWS and CHANGE_TO_AWS <= self.fin:
            "return timerange(self.inicio, CHANGE_TO_AWS + timedelta(hours=-1))"
            "timerange(CHANGE_TO_AWS, self.fin)"     

    def __log(self, string):
        self.console.print(string)

    def __str__(self) -> str:
        return (
            f"  Goes \n"
            f"  Dates: {self.inicio}x{self.fin}\n"
            f"  Path: {self.path}\n"
            f"  Datelist: {self.datelist}\n"
            f"  CPUs: {self.cpu}\n"
        )

    #    def forward_traking

    @recursive_repr()
    def _repr_html_(self) -> str:

        html = [f"Goes class: hours: {len(list(self.datelist))}"]
        return "\n".join(html)
