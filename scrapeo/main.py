import sys
from goes import Goes

if __name__ == "__main__":
    satelite = Goes("2018-07-18", "20")
    #satelite.descarga(dia=True)
    satelite.descarga()
    satelite.__mro__

