from calendar import isleap
from datetime import datetime, timedelta
import os
from time import perf_counter
from bs4 import BeautifulSoup
import requests
from rich.progress import Progress, Console, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn, TransferSpeedColumn

def _links(producto="ABI-L2-CMIPF"):
    XML = {"aws": f"https://noaa-goes16.s3.amazonaws.com/?list-type=2&delimiter=%2F&prefix={producto}%2F",
           "noaa": "https://www.ncei.noaa.gov/data/gridsat-goes/access/goes/"
           }
    
    return XML

class Goes():
    """Clase que chequea los archivos disponibles y tambien gestiona la descarga de los satelites."""

    def __init__(self, fecha: str, horas=None, *, path):
        self._anno = fecha.split("-")[0]
        self._dia = self._convertir_datatime(fecha)
        self._horas = self.__procesar_hora(horas)
        self._hora = None
        #self.__log(f"fecha ingresada: {self._anno}-{self.dia if self.dia else ''}-{self._hora if self._hora else ''}")
        self.__XML = _links()["aws"]
        self.__path = path
        self._path = path
        self.console = Console()
        self.path = [self.anno]
        try:
            os.mkdir(self.path)
        except FileExistsError:
            self.__log(f"El directorio {self.path} ya existe")
        self.path = [self._reconvertir_dia(self.dia)]
        try:
            os.mkdir(self.path)
        except FileExistsError:
            self.__log(f"El directorio {self.path} ya existe")

    def __log(self, string):
        self.console.log(string)

    def __procesar_hora(self, horas) -> list[str]:
        if isinstance(horas, str):
            if "-" in horas:
                start, end = map(int, horas.split('-'))
                horas = list(range(start, end + 1))
            elif horas.isdigit():
                horas = [horas]
        elif not horas:
            horas = [num for num in range(24)]
        return [self.__formato(hora, hora=True) for hora in horas]
    
    def __formato(self, num, dia=None, hora=None) -> str:
        if dia and 1 <= int(num) <= 365:
            return f"{int(num):03}"
        elif dia and isleap(self.anno) and 1 <= int(num) <= 366:
            return f"{int(num):03}"
        elif hora and 0 <= int(num) <= 23 :
            return f"{int(num):02}"
        else:
            raise ValueError("Verifica el dia o la hora")

    def __procesar_xml(self, fecha: tuple) -> BeautifulSoup:
        """Procesa los xml de la pagina de aws y verificar la conexion"""

        self.anno, self.dia, self.hora = fecha
        url = self.XML + \
            f"{str(self.anno) + f'%2F' if self.anno else ''}" + \
            f"{str(self.dia) + f'%2F' if self.dia else ''}" + \
            f"{str(self.hora) + f'%2F' if self.hora else ''}"
        response = requests.get(url)    
        if response.status_code == 200:
            return BeautifulSoup(response.text, features="xml")
        else:
            raise ConnectionError("Conexion no establecida, intentar de nuevo")

    def listar_annos(self, *, return_=False):
        "Lista los años disponibles"
        soup = self.__procesar_xml(fecha=(None for _ in range(3)))
        lista = [annos.text for annos in soup.find_all("CommonPrefixes")]
        self.__log(f"Hay {len(lista)} años de datos disponibles en la pagina:")
        if return_:
            return lista
        for annos in lista:
            self.__log(f"Año: {annos.split("/")[1]}") 
        
    def listar_dias(self, *, return_=False):
        if self.anno is None:
            raise NameError("Define un año")
        soup = self.__procesar_xml(fecha=(self.anno, None, None))
        lista = [dia.text for dia in soup.find_all("CommonPrefixes")]
        self.__log(f"Hay {len(lista)} dias de datos disponibles en el año {self.anno}:")
        if return_:
            return lista
        for dia in lista:
            dia = dia.split("/")[2]
            self.__log(f"Dia: {dia}  {self.anno + "-" + self._reconvertir_dia(dia)}")
    
    def listar_horas(self, *, return_=False):
        if self.anno is None or self.dia is None:
            raise NameError("Define un año y dia")
        soup = self.__procesar_xml(fecha=(self.anno, self.dia, None))
        lista = [hora.text for hora in soup.find_all("CommonPrefixes")]
        self.__log(f"""
                 Hay {len(lista)} horas de datos disponibles en el año
                {self.anno} y dia {self.dia} - {self._reconvertir_dia(self.dia)}:
                """)
        if return_:
            return lista
        for hora in lista:
            self.__log(f"hora: {hora.split("/")[3]}")

    def listar_imagenes(self, *, return_=False):
        if self.anno is None or self.dia is None or self.hora is None:
            raise NameError("Define un año, dia y hora")
        soup = self.__procesar_xml(fecha=(self.anno, self.dia, self.hora))
        lista = [imagen.find("Key").text for imagen in soup.find_all("Contents")]
        self.__log(f"""Hay {len(lista)} imagenes de datos disponibles en el 
        año: {self.anno}, dia: {self._reconvertir_dia(self.dia)}, hora: {self.hora}""")
        if return_:
            return lista
        for imagen in lista:
            self.__log(f"imagen: {imagen.split("/")[4]}")
        
    def __descarga(self, link: str):
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

    def descargar(self):
        """Descarga las imagenes de acuerdo a la fecha, si la fecha ingresada no se 
        especifico una hora u horas, entonces descargará todas las imagenes de ese dia."""
        inicio = perf_counter()
        for hora in self.horas:
            self.hora = hora
            self.path = [hora]
            try:
                os.mkdir(self.path)
                self.__log(f"creando directorio: {self.anno}-{self._reconvertir_dia(self.dia)}-{hora}")
            except FileExistsError:
                self.__log(f"El directorio {self.path} ya existe")
            lista_imagenes = self.listar_imagenes(return_=True)
            for imagen in lista_imagenes:
                #self.__descarga(imagen)
                pass

        fin = perf_counter()
        self.__log(f"Se demoro {(fin - inicio)/60} minutos")

    def _convertir_datatime(self, fecha: str) -> str:
        return str(datetime.strptime(fecha, "%Y-%m-%d").timetuple().tm_yday)
    
    @property
    def anno(self):
        return self._anno
    
    @anno.setter
    def anno(self, anno):
        self._anno = anno

    @property
    def hora(self):
        return self._hora
    
    @hora.setter
    def hora(self, hora):
        self._hora = hora
    
    @property
    def dia(self):
        return self._dia

    @dia.setter
    def dia(self, dia):
        self._dia = dia
        
    @property
    def horas(self):
        return self._horas
        
    @property
    def path(self):
        return self._path
    
    @path.setter
    def path(self, dirs):
        if isinstance(dirs, list):
            path = self._path
            for dir in dirs:
                path = os.path.join(path, dir)
            self._path = path
        else:
            self._path = self.__path

    @property
    def XML(self):
        return self.__XML
    
    def _reconvertir_dia(self, dia: str):
        "input: dia entre 0 y 365, output: mismo dia en formato mes-dia"
        dia = datetime(year=int(self.anno), month=1, day=1) + timedelta(int(dia)-1)
        return dia.strftime("%m-%d")
    

"""
Utiliza esto https://stackoverflow.com/questions/3033952/threading-pool-similar-to-the-multiprocessing-pool
para hacer un pool de threads
y luego utiliza lo que esta en core_processing.py para ver como implementarlo con rich.progress
"""
