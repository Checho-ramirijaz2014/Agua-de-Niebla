import time
from functools import wraps

def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.perf_counter()
        res = func(*args, **kwargs)
        fin = time.perf_counter()
        print(f"{(func.__name__)} se demoro {fin - inicio}")
        return 
    return wrapper

@timeit
def productoria(num):
    result = 1
    for x in range(1, num):
        result = result * x

    print(result)

def __procesar_hora(horas) -> list[str]:
        assert isinstance(horas, (str, list))
        if isinstance(horas, str):
            if '-' in horas:
                start, end = map(int, horas.split('-'))
                horas = list(range(start, end + 1))
            elif horas.isdigit():
                horas = [horas]
        elif not horas:
            horas = [str(num) for num in range(23)]
        return horas

#print(__procesar_hora(None))
def lesear(args):
    if args:
        a = ""
        for arg in args:
            a = a + arg
        print(a)
    else:
        print("No shit")
a = ["a", "b", "c"]
lesear(a)