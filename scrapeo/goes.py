from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
import os
from tqdm import tqdm
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn, TransferSpeedColumn


class Goes():
    def __init__(self, fecha: str, hora: str):

        self._anno = int(fecha.split("-")[0])
        self._dia = int(self._obtener_dia(fecha))
        self._hora = int(hora) if hora else None
        #print(f"fecha ingresada: {self._anno}-{self._dia if self._dia else ''}-{self._hora if self._hora else ''}")
        self.XML = f"https://noaa-goes16.s3.amazonaws.com/?list-type=2&delimiter=%2F&prefix=ABI-L2-CMIPF%2F"
        self._path = os.path.expanduser(os.path.join("~", "Desktop", "goes-images", 
                f"{self.anno}-{self.dia}-{self.hora}"))
    
    def __formato(self, num: int, dia=None, hora=None) -> str:
        assert isinstance(num, (int, str))
        if dia and 1 <= int(num) <= 365:
            return f"{num:03}" 
        elif hora and 0 <= int(num) <= 23 :
            return f"{num:02}"
        else:
            raise ValueError("Verifica el dia o la hora")

    def __procesar_xml(self, fecha: tuple) -> BeautifulSoup:
        self._anno, self._dia, self._hora = fecha
        self._dia = self.__formato(self._dia, dia = True) if self._dia is not None else None
        self._hora = self.__formato(self._hora, hora = True) if self._hora is not None else None
        url = self.XML + \
            f"{str(self._anno) + f'%2F' if self._anno else ''}" + \
                f"{str(self._dia) + f'%2F' if self._dia else ''}" + \
            f"{str(self._hora) + f'%2F' if self._hora else ''}"
        response = requests.get(url)
        if response.status_code == 200:
            return BeautifulSoup(response.text, features="xml")
        else:
            raise ConnectionError("Conexion no establecida, intentar de nuevo")

    def listar_annos(self, enumerar=False, _return=False):
        soup = self.__procesar_xml(fecha=(None for x in range(3)))
        lista = [annos.text for annos in soup.find_all("CommonPrefixes")]
        print(f"Hay {len(lista)} años de datos disponibles en la pagina:")
        if enumerar:
            for annos in lista:
                print(f"Año: {annos.split("/")[1]}") 
        elif _return:
            return lista
        
    def listar_dias(self, enumerar=False, _return=False):
        if self._anno is None:
            raise NameError("Define un año")
        soup = self.__procesar_xml(fecha=(self._anno, None, None))
        lista = [dia.text for dia in soup.find_all("CommonPrefixes")]
        print(f"Hay {len(lista)} dias de datos disponibles en el año {self._anno}:")
        if enumerar:
            for dia in lista:
                print(f"Dia: {dia.split("/")[2]}")
        elif _return:
            return lista
    
    def listar_horas(self, enumerar=False, _return=False):
        if self._anno is None or self._dia is None:
            raise NameError("Define un año y dia")
        soup = self.__procesar_xml(fecha=(self._anno, self._dia, None))
        lista = [hora.text for hora in soup.find_all("CommonPrefixes")]
        print(f"Hay {len(lista)} horas de datos disponibles en el año {self._anno} y dia {self._dia}:")
        if enumerar:
            for hora in lista:
                print(f"hora: {hora.split("/")[3]}")
        elif _return:
            return lista

    def listar_imagenes(self, enumerar=False, _return=False) -> list:
        if self._anno is None or self._dia is None or self._hora is None:
            raise NameError("Define un año, dia y hora")
        soup = self.__procesar_xml(fecha=(self._anno, self._dia, self._hora))
        lista = [imagen.find("Key").text for imagen in soup.find_all("Contents")]
        print(f"""Hay {len(lista)} imagenes de datos disponibles en el 
        año: {self._anno}, dia: {self._dia}, hora: {self._hora}""")
        if enumerar:
            for imagen in lista:
                print(f"imagen: {imagen.split("/")[4]}")
        elif _return:
            return lista
        
    def _descarga(self, link):
        response = requests.get(f"https://noaa-goes16.s3.amazonaws.com/{link}")
        total = int(response.headers.get('content-length', 0))
        self._path = os.path.expanduser(os.path.join("~", "Desktop", "goes-images", 
                f"{self._anno}-{self._dia}-{self._hora}"))
        try:
            os.mkdir(self._path)
            print(f"creando directorio: {self._anno}-{self._dia}-{self._hora}")
        except FileExistsError:
            print(f"El directorio {self._path} ya existe")
        total_length = int(response.headers.get('content-length', 0))
        with open(os.path.join(self._path, link.split("/")[-1]), 'wb') as file, Progress(
            TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
            BarColumn(bar_width=None),
            "•",
            "[progress.percentage]{task.percentage:>3.0f}%",
            "•",
            TransferSpeedColumn(),  # Shows download speed
            "•",
            TimeRemainingColumn(),  # Shows time remaining
            "•",
            TimeElapsedColumn()    # Shows elapsed time
        ) as progress: 
            download_task = progress.add_task("[cyan]Descargando...", total=total_length, filename=link)
            for chunk in response.iter_content(chunk_size=4096):  
                file.write(chunk)
                progress.update(download_task, advance=len(chunk), refresh=True) 

    def descarga(self, dia=None, hora=None):
        if self._dia:
            #lista_hora = 18 #self.listar_horas(_return=True)
            #for hora in lista_hora:
            #   self._hora = 18 #hora.split("/")[3]
            try:
                os.mkdir(self._path)
                print(f"creando directorio: {self.anno}-{self.dia}-{self.hora}")
            except FileExistsError:
                print(f"El directorio {self._path} ya existe")
            lista_imagenes = self.listar_imagenes(_return=True)
            for imagen in lista_imagenes:
                self._descarga(imagen)

    def _obtener_dia(self, fecha: str):
        return datetime.strptime(fecha, "%Y-%m-%d").timetuple().tm_yday
    
    @property
    def anno(self):
        return str(self._anno)
    
    @property
    def dia(self):
        return str(self.__formato(self._dia, dia=True))
    
    @property
    def hora(self):
        return str(self.__formato(self._hora, hora=True))
    
    
    