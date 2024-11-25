import xarray as xr
import os
import numpy as np
#from pyproj import Transformer

coords = np.array([-85, -10])

coordenates = np.array([[-85, -60], #longitude = x
                        [-10, -40]]) #latitude = y

coordenates_r = {
    "latup": -0.03057186,
    "latdown": -0.10849813,
    "lonleft": -0.03029632,
    "lonright": 0.03361291
}

example_coordenates = np.array([np.float64(-84.690932), np.float64(33.846162)])

def _clipping_images(image: str): 
    ds = xr.open_dataset(image)
    
    #clips the image according to the coords

    subset = ds.sel(
        x=slice(coordenates_r["latdown"], coordenates_r["latup"]),
        y=slice(coordenates_r["lonleft"], coordenates_r["lonright"])
    )
    print(ds)

    #subset.to_netcdf(image.strip("OR_"))

def grados_d(num):
     return np.format_float_positional(np.float64(num), precision=6)

def convertir_radianes_a_grados(vector: np.array):
    x_coordinate = vector[0] * np.pi / 180.0 #longitud 
    y_coordinate = vector[1] * np.pi / 180.0 #latitud 
    
    lambda_0 = -89.5 * np.pi / 180.0

    H = 42_164_160 #meters

    E = np.float64(0.0818_191_910_435) #first eccentricity

    r_pol = np.float64(6_356_752.31_414) #true
    r_eq = 6_378_137 #true

    phi_c = np.arctan((r_pol / r_eq) * (r_pol / r_eq) * np.tan(y_coordinate)) # geocentric latitude

    r_c = r_pol / (np.sqrt(1 - E * E * np.cos(phi_c) * np.cos(phi_c))) # geocentric distance to the point on ellipsoid

    s_x = (H - r_c * np.cos(phi_c) * np.cos(x_coordinate - lambda_0))

    s_y = -r_c * np.cos(phi_c) * np.sin(x_coordinate - lambda_0)

    s_z = r_c * np.sin(phi_c)

    y = np.arctan(s_z / s_x)
    x = np.arcsin(-s_y / np.sqrt(s_x * s_x + s_y * s_y + s_z * s_z))

    return x, y


print(f"""
longitud (x): {convertir_radianes_a_grados(coords)[0]}
latitud (y): {convertir_radianes_a_grados(coords)[1]}
""")