import multiprocessing as mp
from time import sleep, perf_counter
from functools import wraps
import xarray

def reintentar(reintento, esperar_reintento=5):
    def timeit(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = perf_counter()
            func(*args, **kwargs)
            end = perf_counter()
            print(f"Se demoro {end-start} segundos en ejecutar")
        return wrapper

@timeit
def sumatoria(n):
    print(n * (n + 1) / 2)

def abrir_nc(path):
    with xarray.open_dataset(path, decode_coords="all") as nc:
        nc.plot.scatter()



abrir_nc("/home/checho/Desktop/goes-images/2018-199-00/OR_ABI-L2-CMIPF-M3C01_G16_s20181990000467_e20181990011234_c20181990011303.nc")


