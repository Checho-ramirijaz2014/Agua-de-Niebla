from goes import Goes


def main():
    satelite = Goes("2018-07-18", "20")
    #satelite.descarga(dia=True)
    satelite.descarga()

if __name__ == "__main__":
    main()
