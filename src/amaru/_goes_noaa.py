from bs4 import BeautifulSoup
import multiprocessing as mp
import os
import requests
from rich.progress import Progress, Console, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn, TransferSpeedColumn

_URL = "https://www.ncei.noaa.gov/data/gridsat-goes/access/goes/"

class _GoesNOAA():

    """Class designed to download images from the noaa page, previous releases from 1994 to 2017"""

    __slots__ = "path", "console", "date", "cpu"

    def __init__(self, date, path, console: Console, cpu):
        self.date = date
        self.path = path
        self.cpu = cpu
        self.console = console

    def _descargar(self) -> None:
        """Gestiona la descarga de una fecha en especifico"""
        lista_imagenes = self._listar_imagenes()

        with mp.Pool(self.cpu) as pool:
            pool.starmap(self._descarga, [(self.path, imagen) for imagen in lista_imagenes])
    

    def __log(self, string):
        self.console.log(string)

    
    def _procesar_html(self) -> BeautifulSoup:
        response = requests.get(_URL + self.date)
        if response.status_code == 200:
            return BeautifulSoup(response.text)
        else:
            raise ConnectionError("Conexion not possible to the ncei noaa servers")

    def _descarga(self) -> None:
        #response = requests.get(_URL + )
        pass

_fecha = "2017/09/" #year + month
_path = os.path.join("/media", "checho", "goes", "2017", "01", "1", "00")
goesito = _GoesNOAA(_fecha, _path, Console(), os.cpu_count())
#goesito._descargar()
goesito._procesar_html()