from bs4 import BeautifulSoup
import multiprocessing as mp
import os
import requests
from .constants import _URLNOAAH
from rich.progress import (
    Progress,
    Console,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
    TransferSpeedColumn,
)


class _GoesNOAA:
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
            pool.starmap(
                self._descarga, [(self.path, imagen) for imagen in lista_imagenes]
            )

    def __log(self, string):
        self.console.log(string)

    def _procesar_html(self) -> BeautifulSoup:
        response = requests.get(_URLNOAAH + self.date)
        if response.status_code == 200:
            return BeautifulSoup(response.text, "html.parser")
        else:
            raise ConnectionError("Conexion not possible to the ncei noaa servers")

    def _listar_imagenes(self) -> list[str]:
        soup = self._procesar_html()
        lista = [row.text for row in soup.find_all("a") if "GridSat-GOES" in row.text]
        self.__log(f"Hay {len(lista)} archivos .nc")
        return lista

    @staticmethod
    def _descarga(path: str, link: str) -> None:

        response = requests.get(
            f"https://noaa-goes16.s3.amazonaws.com/{link}", stream=True
        )
        total_length = int(response.headers.get("content-length", 0))

        file = open(os.path.join(path, link.split("/")[-1]), "wb")

        progress = Progress(
            TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
            BarColumn(bar_width=None),
            "•",
            "[progress.percentage]{task.percentage:>3.0f}%",
            "•",
            TransferSpeedColumn(),  # Muestra velocida de progresso de descarga
            "•",
            TimeRemainingColumn(),  # Muestra el tiempo que falta
            "•",
            TimeElapsedColumn(),  # muestra el tiempo que ha transcurrido
        )

        with file, progress:
            task_descarga = progress.add_task(
                "[cyan]Descargando...", total=total_length, filename=link.split("/")[-1]
            )
            for chunk in response.iter_content(chunk_size=4096):
                file.write(chunk)
                progress.update(task_descarga, advance=len(chunk), refresh=True)


_fecha = "2015/01/"  # year + month
_path = os.path.join(
    "/run", "media", "checho", "disco para la u", "goes", "2015", "01", "1", "00"
)
goesito = _GoesNOAA(_fecha, _path, Console(), os.cpu_count())
# goesito._descargar()
goesito._descargar()
