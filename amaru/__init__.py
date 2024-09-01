from .goes import Goes


__author__ = "Sergio Ramírez"
__email__ = "sergio.ramrez@uc.cl"
__version__ = 1.2

try:
    import rich

except ImportError:
    print("rich no esta instalado")
    print("instalar con pip install rich")
