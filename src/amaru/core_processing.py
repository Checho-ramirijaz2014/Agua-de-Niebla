import time
from functools import wraps, partial
import multiprocessing as mp


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.perf_counter()
        res = func(*args, **kwargs)
        fin = time.perf_counter()
        print(f"{(func.__name__)} se demoro {fin - inicio}")
        return res

    return wrapper


@timeit
def productoria(num):
    result = 1
    for x in range(1, num):
        result = result * x

    print(result)
