from amaru import Goes
import os


def main():
    #satelite = Goes("2018-07-18", "3")
    satelite = Goes("2024-05-09",
    path=os.path.expanduser(
        os.path.join("~", "Desktop", "goes-images"
)))
    satelite.descargar()

if __name__ == "__main__":
    main()
