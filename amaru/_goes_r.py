
from bs4 import BeautifulSoup
import os
import requests
from rich.progress import Progress, Console, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn, TransferSpeedColumn

_XML = "https://noaa-goes16.s3.amazonaws.com/"

class _GoesAWS():
    """Clase que administra las descargas de la pagina de AWS"""

    __slots__ = "path", "console", "payload"

    def __init__(self, date: str, path, console: Console, product="ABI-L2-CMIPF"):
        self.path = path
        self.console = console

        self.payload = {
            "list-type": "2",
            "delimiter": "/",
            "prefix": f"{product}/{date}"
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
        
    def _listar_imagenes(self):
        soup = self._procesar_xml()
        lista = [imagen.find("Key").text for imagen in soup.find_all("Contents")]
        self.__log(f"Hay {len(lista)} imagenes de datos disponibles")
        return lista
        
    def _descargar(self, year, day, hour)-> None:
        """Gestiona la descarga de una fecha en especifico"""
        try:
            os.mkdir(self.path)
        except FileExistsError:
            self.__log(f"creando directorio: {year}-{day.replace("/", "-")}-{hour}")
    
        lista_imagenes = self._listar_imagenes()
        for imagen in lista_imagenes:
            self._descarga(imagen)

    def _descarga(self, link: str):
        response = requests.get(f"https://noaa-goes16.s3.amazonaws.com/{link}")
        total_length = int(response.headers.get('content-length', 0))
        with open(os.path.join(self.path, link.split("/")[-1]), 'wb') as file, Progress(
             TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
             BarColumn(bar_width=None),
             "•", "[progress.percentage]{task.percentage:>3.0f}%",
             "•", TransferSpeedColumn(),  # Muestra velocida de progresso de descarga
             "•", TimeRemainingColumn(),  # Muestra el tiempo que falta
             "•", TimeElapsedColumn()    # muestra el tiempo que ha transcurrido
        ) as progress: 
            task_descarga = progress.add_task("[cyan]Descargando...", total=total_length, filename=link)
            for chunk in response.iter_content(chunk_size=4096):  
                file.write(chunk)
                progress.update(task_descarga, advance=len(chunk), refresh=True) 

goesito = _GoesAWS(
    "2022/050/09/",
    os.path.expanduser(
        os.path.join("~", "Desktop", "goes-images"
    )),
    Console()
)
goesito._descargar("2022", "19/2", "9")

