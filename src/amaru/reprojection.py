"""
GOES-16 NetCDF reprojection script
Converts GOES-16 ABI data from geostationary to geographic projection
"""

import os
import sys
from datetime import datetime
from osgeo import gdal, osr
import numpy as np
from functools import partial
import multiprocessing as mp
from .constants import *
from pathlib import Path
import xarray as xr

gdal.UseExceptions()

try:
    import netCDF4

    HAS_NETCDF4 = True
except ImportError:
    HAS_NETCDF4 = False
    print("Warning: netCDF4 not available. Metadata updates will be limited.")

def unclipped_file(directory: str) -> list[str]:
    dir_ = Path(directory)
    return [
        str(file) for file in dir_.rglob('*.nc')
        if not file.name.endswith('_clipped.nc')
    ]

def reproject_goes16(input_file, output_file=None):
    """
    Reproject GOES-16 netCDF file from geostationary to geographic projection
    
    Args:
        input_file (str): Path to input GOES-16 netCDF file
        output_file (str): Path to output file (optional)
    """
    
    # Configure output file name
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_test.nc"
    
    # Target projection parameters
    target_srs = "EPSG:4326"  # WGS84 Geographic   
    
    print(f"Processing GOES-16 file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Target bounds: {XMIN:.6f}, {YMIN:.6f}, {XMAX:.6f}, {YMAX:.6f}")
    print(f"Resolution: {XRES:.6f}, {YRES:.6f}")
    print(f"Dimensions: {WIDTH}x{HEIGHT}")
    
    # Construct subdataset name
    subdataset = f'NETCDF:"{input_file}":CMI'
    
    # Configure GDAL warp options for NetCDF3 Classic
    warp_options = gdal.WarpOptions(
        format='NetCDF',
        dstSRS=target_srs,
        outputBounds=[XMIN, YMIN, XMAX, YMAX],
        xRes=XRES,
        yRes=YRES,
        width=WIDTH,
        height=HEIGHT,
        resampleAlg=None,
        srcNodata=np.nan,
        dstNodata=np.nan,
        outputType=gdal.GDT_Float64,
        
        creationOptions=[
            'FORMAT=NC',
            'WRITE_BOTTOMUP=NO',
            'COMPRESS=NONE'  # NetCDF3 doesn't support compression
        ]
    )
    
    try:
        # Perform the reprojection to temporary file first
        print("Reprojecting data...")
        temp_file = output_file + ".temp"
        result = gdal.Warp(temp_file, subdataset, options=warp_options)
        
        if result is None:
            raise Exception("GDAL Warp failed")
        
        result = None  # Close the dataset
        
        print("Converting to NetCDF3 Classic format...")
        
        # Convert to NetCDF3 Classic using netCDF4-python
        convert_to_netcdf3_classic(temp_file, output_file, rename_band=('Band1', 'CMI'))
        
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        print("Conversion complete. Updating metadata...")
        
        # Update metadata
        update_metadata(output_file)
        
        print("Processing complete!")
        print(f"Output file: {output_file}")
        
        # Display output file info
        print("\n=== Output file information ===")
        display_info(output_file)
            
    except Exception as e:
        print(f"Error: {e}")

def convert_to_netcdf3_classic(input_file, output_file, rename_band=None):
    """
    Convert NetCDF file to NetCDF3 Classic format
    
    Args:
        input_file (str): Input NetCDF file
        output_file (str): Output NetCDF3 Classic file
        rename_band (tuple): Optional tuple of (old_name, new_name) to rename a variable
    """
    
    if not HAS_NETCDF4:
        raise Exception("netCDF4 library required for NetCDF3 conversion")
    
    print(f"Converting {input_file} to NetCDF3 Classic format...")
    
    
    with netCDF4.Dataset(input_file, 'r') as src:
        
        with netCDF4.Dataset(output_file, 'w', format='NETCDF3_CLASSIC') as dst:
            
            # Copy global attributes safely
            for attr_name in src.ncattrs():
                try:
                    attr_value = src.getncattr(attr_name)
                    
                    # Handle different attribute types for NetCDF3 compatibility
                    if isinstance(attr_value, str):
                        dst.setncattr(attr_name, attr_value)
                    elif isinstance(attr_value, (int, np.integer)):
                        dst.setncattr(attr_name, int(attr_value))
                    elif isinstance(attr_value, (float, np.floating)):
                        dst.setncattr(attr_name, float(attr_value))
                    elif isinstance(attr_value, np.ndarray):
                        if attr_value.size == 1:
                            # Single value array
                            val = attr_value.item()
                            if isinstance(val, (int, np.integer)):
                                dst.setncattr(attr_name, int(val))
                            elif isinstance(val, (float, np.floating)):
                                dst.setncattr(attr_name, float(val))
                            else:
                                dst.setncattr(attr_name, str(val))
                        else:
                            # Multiple values - convert to list
                            dst.setncattr(attr_name, attr_value.tolist())
                    else:
                        # Try to convert to string as fallback
                        dst.setncattr(attr_name, str(attr_value))
                        
                except Exception as e:
                    print(f"Warning: Could not copy global attribute '{attr_name}': {e}")
                    continue
            
            # Copy dimensions
            for dim_name, dim in src.dimensions.items():
                dst.createDimension(dim_name, len(dim) if not dim.isunlimited() else None)
            
            # Copy variables
            for var_name, var in src.variables.items():
                
                # Check if this variable should be renamed
                output_var_name = var_name
                if rename_band and var_name == rename_band[0]:
                    output_var_name = rename_band[1]
                    print(f"Renaming variable '{var_name}' to '{output_var_name}'")
                
                # Determine appropriate data type for NetCDF3
                dtype = var.dtype
                if dtype == np.float64:
                    nc_dtype = 'f8'  # double
                elif dtype == np.float32:
                    nc_dtype = 'f4'  # float
                elif dtype == np.int32:
                    nc_dtype = 'i4'  # int
                elif dtype == np.int16:
                    nc_dtype = 'i2'  # short
                else:
                    nc_dtype = 'f8'  # default to double
                
                # Check for fill value safely
                fill_value = None
                try:
                    if hasattr(var, '_FillValue'):
                        fill_value = var._FillValue
                    elif 'missing_value' in var.ncattrs():
                        fill_value = var.getncattr('missing_value')
                    elif '_FillValue' in var.ncattrs():
                        fill_value = var.getncattr('_FillValue')
                except (AttributeError, KeyError):
                    pass
                
                # Create variable
                dst_var = dst.createVariable(
                    output_var_name,  # Use the potentially renamed variable name
                    nc_dtype, 
                    var.dimensions,
                    zlib=False,  # No compression in NetCDF3
                    fill_value=fill_value
                )
                
                # Copy variable attributes safely
                for attr_name in var.ncattrs():
                    if attr_name in ['_FillValue']:  # Skip fill value, already handled
                        continue
                        
                    try:
                        attr_value = var.getncattr(attr_name)
                        
                        # Handle different attribute types for NetCDF3 compatibility
                        if isinstance(attr_value, str):
                            dst_var.setncattr(attr_name, attr_value)
                        elif isinstance(attr_value, (int, np.integer)):
                            dst_var.setncattr(attr_name, int(attr_value))
                        elif isinstance(attr_value, (float, np.floating)):
                            # Handle NaN values
                            if np.isnan(attr_value):
                                dst_var.setncattr(attr_name, np.nan)
                            else:
                                dst_var.setncattr(attr_name, float(attr_value))
                        elif isinstance(attr_value, np.ndarray):
                            if attr_value.size == 1:
                                # Single value array
                                val = attr_value.item()
                                if isinstance(val, (int, np.integer)):
                                    dst_var.setncattr(attr_name, int(val))
                                elif isinstance(val, (float, np.floating)):
                                    dst_var.setncattr(attr_name, float(val))
                                else:
                                    dst_var.setncattr(attr_name, str(val))
                            else:
                                # Multiple values - convert to list
                                dst_var.setncattr(attr_name, attr_value.tolist())
                        else:
                            # Try to convert to string as fallback
                            dst_var.setncattr(attr_name, str(attr_value))
                            
                    except Exception as e:
                        print(f"Warning: Could not copy attribute '{attr_name}' for variable '{var_name}': {e}")
                        continue
                
                # Copy data
                try:
                    dst_var[:] = var[:]
                except Exception as e:
                    print(f"Warning: Could not copy data for variable '{var_name}': {e}")
                    continue


    
    print(f"Successfully converted to NetCDF3 Classic: {output_file}")

    
    print("--- Removing unnecesary data... ---")

    # global metadata
    with netCDF4.Dataset(output_file, "a") as ds:
        del ds.project
        del ds.cdm_data_type
        del ds.dataset_name
        del ds.date_created
        del ds.GDAL
        del ds.id
        del ds.instrument_ID
        del ds.instrument_type
        del ds.iso_series_metadata_id
        del ds.keywords
        del ds.keywords_vocabulary
        del ds.license
        del ds.Metadata_Conventions
        del ds.naming_authority
        del ds.orbital_slot
        del ds.platform_ID
        del ds.processing_level
        del ds.production_data_source
        del ds.production_environment
        del ds.production_site
        del ds.scene_id
        del ds.spatial_resolution
        del ds.standard_name_vocabulary
        del ds.summary
        del ds.timeline_id
        del ds.time_coverage_end
        del ds.time_coverage_start
        del ds.institution

        # cmi metadata
        cmi_data = ds.variables["CMI"]
        del cmi_data.resolution
        # del cmi_data.add_offset
        del cmi_data.ancillary_variables
        del cmi_data.grid_mapping
        del cmi_data.standard_name
        del cmi_data.sensor_band_bit_depth
        # del cmi_data.scale_factor
        del cmi_data.cell_methods
        del cmi_data._FillValue

        # latitude metadata
        lat_data = ds.variables["lat"]
        del lat_data.long_name
        del lat_data.standard_name
        
        # longitude metadata
        lon_data = ds.variables["lon"]
        del lon_data.long_name
        del lon_data.standard_name

    print("metadata removed sucesfully")


def update_metadata(output_file):
    """
    Update NetCDF metadata to match target format
    
    Args:
        output_file (str): Path to output NetCDF file
    """
    
    if not HAS_NETCDF4:
        print("Skipping detailed metadata updates (netCDF4 not available)")
        return
    
    try:
        # Open NetCDF file for editing in NetCDF3 Classic format
        with netCDF4.Dataset(output_file, 'r+', format='NETCDF3_CLASSIC') as nc:
            
            # Update global attributes
            nc.setncattr('Conventions', 'CF-1.0')
            nc.setncattr('title', 'ABI L2+ Cloud and Moisture Imagery reflectance factor')
            
            # Add geographic datum information
            esri_prj = ('GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",'
                       'SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],'
                       'UNIT["Degree",0.0174532925199433]]')
            nc.setncattr('geographic_datum_ESRI_PRJ', esri_prj)
            
            ogc_wkt = ('GEOGCS["NAD83", DATUM["NAD83", SPHEROID["GRS_1980", 6378137.0, '
                      '298.25722210100002],TOWGS84[0,0,0,0,0,0,0]], PRIMEM["Greenwich", 0.0], '
                      'UNIT["degree",0.017453292519943295], AXIS["Longitude",EAST], '
                      'AXIS["Latitude",NORTH]]')
            nc.setncattr('geographic_datum_OGC_WKT', ogc_wkt)
            
            # Add processing history
            export_date = datetime.now().strftime("%a %b %d %H:%M:%S GMT%z %Y")
            history = (f"Exported to NetCDF-3 CF-1.0 conventions by the NOAA Weather and "
                      f"Climate Toolkit (version 4.8.0)  Export Date: {export_date}")
            nc.setncattr('History', history)
            
            # Find the data variable (usually 'Band1' after GDAL processing)
            data_vars = [var for var in nc.variables.keys() 
                        if var not in ['lon', 'lat', 'x', 'y', 'longitude', 'latitude', 
                                      'crs', 'spatial_ref']]
            
            if data_vars:
                var_name = data_vars[0]  # Take the first data variable
                print(f"Updating variable metadata for: {var_name}")
                
                var = nc.variables[var_name]
                var.setncattr('long_name', 'ABI L2+ Cloud and Moisture Imagery reflectance factor')
                var.setncattr('units', '1')
                var.setncattr('missing_value', np.nan)
                
                # Update variable name in metadata
                if hasattr(var, 'NETCDF_VARNAME'):
                    var.setncattr('NETCDF_VARNAME', 'CMI')
            
            # Add coordinate variable attributes if they exist
            if 'lat' in nc.variables:
                lat_var = nc.variables['lat']
                lat_var.setncattr('datum', 'NAD83 - NOAA Standard')
                lat_var.setncattr('spacing', 0.03753753753753754)
                lat_var.setncattr('units', 'degrees_north')
            
            if 'lon' in nc.variables:
                lon_var = nc.variables['lon']
                lon_var.setncattr('datum', 'NAD83 - NOAA Standard')
                lon_var.setncattr('spacing', 0.03753753753753754)
                lon_var.setncattr('units', 'degrees_east')
            
    except Exception as e:
        print(f"Warning: Could not update all metadata: {e}")

def display_info(filename):
    """
    Display GDAL info for the output file
    
    Args:
        filename (str): Path to file
    """
    
    try:
        dataset = gdal.Open(filename)
        if dataset is None:
            print(f"Could not open {filename}")
            return
        
        # Get basic info
        print(f"Driver: {dataset.GetDriver().GetDescription()}")
        print(f"Files: {filename}")
        print(f"Size is {dataset.RasterXSize}, {dataset.RasterYSize}")
        
        # Get geotransform
        gt = dataset.GetGeoTransform()
        if gt:
            print(f"Origin = ({gt[0]},{gt[3]})")
            print(f"Pixel Size = ({gt[1]},{gt[5]})")
        
        # Get projection info
        proj = dataset.GetProjection()
        if proj:
            srs = osr.SpatialReference(wkt=proj)
            print(f"Coordinate System is:")
            print(srs.ExportToPrettyWkt())
        
        # Get corner coordinates
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        
        transform = dataset.GetGeoTransform()
        if transform:
            def pixel_to_coord(x, y):
                x_coord = transform[0] + x * transform[1] + y * transform[2]
                y_coord = transform[3] + x * transform[4] + y * transform[5]
                return x_coord, y_coord
            
            print("Corner Coordinates:")
            ul_x, ul_y = pixel_to_coord(0, 0)
            print(f"Upper Left  ( {ul_x:>12.7f}, {ul_y:>12.7f})")
            
            ll_x, ll_y = pixel_to_coord(0, rows)
            print(f"Lower Left  ( {ll_x:>12.7f}, {ll_y:>12.7f})")
            
            ur_x, ur_y = pixel_to_coord(cols, 0)
            print(f"Upper Right ( {ur_x:>12.7f}, {ur_y:>12.7f})")
            
            lr_x, lr_y = pixel_to_coord(cols, rows)
            print(f"Lower Right ( {lr_x:>12.7f}, {lr_y:>12.7f})")
            
            center_x, center_y = pixel_to_coord(cols/2, rows/2)
            print(f"Center      ( {center_x:>12.7f}, {center_y:>12.7f})")
        
        # Band information
        for i in range(dataset.RasterCount):
            band = dataset.GetRasterBand(i + 1)
            print(f"Band {i+1} Block={band.GetBlockSize()[0]}x{band.GetBlockSize()[1]} "
                  f"Type={gdal.GetDataTypeName(band.DataType)}, ColorInterp={band.GetColorInterpretation()}")
            
            nodata = band.GetNoDataValue()
            if nodata is not None:
                print(f"  NoData Value={nodata}")
            
            unit = band.GetUnitType()
            if unit:
                print(f"  Unit Type: {unit}")
            
            # Metadata
            metadata = band.GetMetadata()
            if metadata:
                print("  Metadata:")
                for key, value in metadata.items():
                    print(f"    {key}={value}")
        
        dataset = None
        
    except Exception as e:
        print(f"Error displaying info: {e}")

def goes_clip(directory: str) -> None:
    """clips .NCs from selected directories"""
    dir_ = Path(directory)
    files = [
        str(file) for file in dir_.rglob('*.nc')
        if not file.name.endswith('_clipped.nc')
    ]