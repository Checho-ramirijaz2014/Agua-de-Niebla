from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as Bs
from selenium.webdriver.chrome.service import Service
from variables import PAGINA
import requests
import time
import os

path_descarga = os.path.join("~", "Desktop", "goes-images")

def formato_dia(num):
    if len(str(num)) == 1:
        num = f"00{num}"
    elif len(str(num)) == 2:
        num = f"0{num}"
    return num

def formato_hora(hora):
    if len(str(hora)) == 1:
        hora = f"0{hora}"
    return hora

#https://noaa-goes16.s3.amazonaws.com/ABI-L2-CMIPF/2020/001/00/OR_ABI-L2-CMIPF-M6C01_G16_s20200010000216_e20200010009524_c20200010010012.nc

driver = webdriver.Firefox()
def iteracion():
#    for num in range(1, 366):
    for dia in range(199, 199):
#        for hora in range(23):
        dia = formato_dia(dia)
        for hora in range(2):
            hora = formato_hora(hora)
            driver.get(f"https://noaa-goes16.s3.amazonaws.com/index.html#ABI-L2-CMIPF/2018/{dia}/{hora}/")
            time.sleep(3)
            urls = driver.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "a")
            links = [url.text for url in urls]



    from scrp import Scrapeo

iteracion()