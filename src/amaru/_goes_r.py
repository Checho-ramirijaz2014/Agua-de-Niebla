from bs4 import BeautifulSoup
import os
import multiprocessing as mp
import requests
from rich.progress import Progress, Console, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn, TransferSpeedColumn

_XML = "https://noaa-goes16.s3.amazonaws.com/"

class _GoesAWS():
    """Clase que administra las descargas de la pagina de AWS"""

    __slots__ = "path", "console", "payload", "cpu"

    def __init__(self, time: str, path, console: Console, product="ABI-L2-CMIPF", cpu=mp.cpu_count()):
        self.path = path
        self.console = console
        self.cpu = cpu

        self.payload = {
            "list-type": "2",
            "delimiter": "/",
            "prefix": f"{product}/{time}/"
        }   

    def __log(self, string):
        self.console.log(string)

    def _procesar_xml(self) -> BeautifulSoup:
        """Procesa los xml de la pagina de aws y verificar la conexion"""
        response = requests.get(_XML, params=self.payload)    
        if response.status_code == 200:
            return BeautifulSoup(response.text, features="xml")
        else:
            raise ConnectionError("Conexion no establecida, intentar de nuevo")
    
    def _listar_imagenes(self) -> list[str]:
        soup = self._procesar_xml()
        lista = [imagen.find("Key").text for imagen in soup.find_all("Contents")]
        self.__log(f"Hay {len(lista)} imagenes de datos disponibles")
        return lista
        
    def _descargar(self) -> None:
        """Gestiona la descarga de una fecha en especifico"""
        lista_imagenes = self._listar_imagenes()

        with mp.Pool(self.cpu) as p:
            p.starmap(self._descarga, [(self.path, imagen) for imagen in lista_imagenes])

    @staticmethod
    def _descarga(path: str,link: str) -> None:

        response = requests.get(f"https://noaa-goes16.s3.amazonaws.com/{link}", stream=True)
        total_length = int(response.headers.get('content-length', 0))

        file = open(os.path.join(path, link.split("/")[-1]), 'wb')

        progress = Progress(
            TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
            BarColumn(bar_width=None),
            "•", "[progress.percentage]{task.percentage:>3.0f}%",
            "•", TransferSpeedColumn(),  # Muestra velocida de progresso de descarga
            "•", TimeRemainingColumn(),  # Muestra el tiempo que falta
            "•", TimeElapsedColumn()    # muestra el tiempo que ha transcurrido
        )

        with file, progress:
            task_descarga = progress.add_task("[cyan]Descargando...", total=total_length, filename=link.split("/")[-1])
            for chunk in response.iter_content(chunk_size=4096):  
                file.write(chunk)
                progress.update(task_descarga, advance=len(chunk), refresh=True) 

_fecha = "2017/060/04"
_path = os.path.join("/media", "checho", "goes", "2017", "03", "1", "04")
goesito = _GoesAWS(_fecha, _path, Console())
goesito._descargar()

