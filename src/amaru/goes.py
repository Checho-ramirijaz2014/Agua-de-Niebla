from datetime import datetime, date, timedelta
from pathlib import Path
import requests
from rich.console import Console
import os
from ._goes_r import _GoesAWS
import warnings


"""fechas posteriores al 28 de febero del 2017 (incluyendo ese dia) estan en el AWS"""
__CHANGE_TO_AWS__ = date(2017, 2, 28) 

class Goes():

    """Clase que chequea los archivos disponibles y tambien gestiona la descarga de los satelites."""

    def __init__(self, inicio: datetime | date, fin: datetime | date, path: str | None=Path().home() / "goes_downloaded", cpu=os.cpu_count()):
        self._inicio = inicio
        self._fin = fin
        self._path = Path(path) 
        self._console = Console(log_time=False)
        self._datelist: tuple = self._time_range()
        self._cpu = cpu

    #Hacer que la clase solo sea de lectura
    
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
    
    def check_noaa(self):
        """checks connection to goes noaa"""
        try:    
            response = requests.get("https://www.ncei.noaa.gov/data/gridsat-goes/access/goes/")
            if response.status_code == 200:
                self.__log("conection to NOAA available")
            else:
                raise requests.exceptions.HTTPError
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
            warnings.warn("Conection not available to NOAA")

    def check_aws(self):
        """checks connection to Goes AWS """
        try:
            response = requests.get("https://noaa-goes16.s3.amazonaws.com/")
            if response.status_code == 200:
                self.__log("Conection to AWS available")
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
            warnings.warn("Conection not available to AWS")

    def _time_range(self) -> tuple:
        if type(self.inicio) != type(self.fin): #si ambos son de tipos distintos
            raise TypeError("Usa solo date o datetime, no ambos a la vez")
        elif self.inicio == self.fin: #si son la misma fecha
            raise RuntimeError("No hay rango de tiempo, seleccionar fechas distintas")
        
        return self.__create_list()
        
    #cuando el objeto es de tipo date
    def __create_list(self) -> tuple:
        diff_day = int((self.fin - self.inicio).days)
        date_list = [self.fin - timedelta(days=day) for day in range(diff_day)]
        return (), date_list, ()
    
    def descargar(self):
        """Descarga las imagenes de acuerdo a la fecha, si en la fecha ingresada no se 
        especifico una hora u horas, entonces se descargará todas las imagenes de ese dia."""
        assert self.datelist[0] == self.datelist[2]

        #for every date download from 0am to 23pm
        for image in self.datelist[1]:
            for hora in range(1,5):
                #check if the image is in aws or noaa
                if __CHANGE_TO_AWS__ <= image:
                    """ordinal representation of a given day
                    example: 246 for 3th september"""
                    day = int(image.strftime("%j"))
                    fecha = f"{image.year}/{day:03}/{hora:02}"

                    path = Path(self.path / str(image.year)
                                / image.strftime(f"%b") / str(image.day)
                                / f"{hora:02}")
                    
                    path.mkdir(parents=True, exist_ok=True)

                    aws = _GoesAWS(fecha, path, self.console, self.cpu)
                    aws._descargar()
                    del aws
                else:
                    pass

    
    def __log(self, string):
        self.console.log(string, sep=os.linesep)

    def __str__(self) -> str:
        pass

    def __repr__(self) -> str:
        pass 
        