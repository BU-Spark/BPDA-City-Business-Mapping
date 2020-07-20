import pandas as pd
import geopandas as gpd
import argparse
import os
import time
from shapely.geometry import Point

import warnings; warnings.filterwarnings('ignore', 'GeoSeries.isna', UserWarning)

'''
Input example:
Takes a spreadsheet from merge.py (or other spreadsheet with latitude and longitude columns)
python <name_of_script> -p <places_spreadsheet> -s <shape_file>
'''

'''
Output example:
The same spreadsheet but with only the points that fall inside a shape from the shape file
'''


# Inputs function
def get_inputs():
    input = argparse.ArgumentParser()
    input.add_argument('-p', '--places_spreadsheet', required=True, help='Spreadsheet containing places of interest '
                                                                         'and their latitude and longitude')
    input.add_argument('-s', '--shape_file_dir', required=True, help='Directory that contains all the relevant files '
                                                                     'including the shape file')
    arguments = vars(input.parse_args())
    return arguments


# Function to create a GeoDataFrame from a DataFrame
def create_gdp(df, latitude='latitude', longitude='longitude'):
    crs = {'init': 'epsg:4326'}
    geometry = [Point(xy) for xy in zip(df[longitude], df[latitude])]
    return gpd.GeoDataFrame(df.copy(), crs=crs, geometry=geometry)


# Given a directory, this function finds the first shape file in the directory
def get_shape_file(shape_file_dir):
    file_list = os.listdir(shape_file_dir)
    for name in file_list:
        if name[-4:] == '.shp':
            return shape_file_dir + '/' + name


# Loads a DataFrame from either csv or xlsx
def load_data_frame(file_name):
    if file_name[-4:] == '.csv':
        return pd.read_csv(file_name)
    elif file_name[-5:] == '.xlsx':
        return pd.read_excel(file_name)


# Takes two GeoDataFrames, one of shapes and one of points and returns the points that fall within the shape
def get_intersection(points, shape):
    intersection = points.intersection(shape.buffer(0).unary_union)

    drop_list = []
    for i in range(len(intersection)):
        comp_bool = intersection.is_empty.iloc[i] | intersection.isna().iloc[i]
        if comp_bool:
            drop_list.append(i)
    return points.drop(drop_list)


def main():
    arguments = get_inputs()

    shape_file_dir = arguments['shape_file_dir']
    shape_file = get_shape_file(shape_file_dir)
    shape = gpd.read_file(shape_file)

    places_name = arguments['places_spreadsheet']
    places = load_data_frame(places_name)
    gplaces = create_gdp(places)
    
    start = time.time()
    
    new_places = get_intersection(gplaces, shape)

    new_places.drop('geometry', axis=1, inplace=True)
    new_name = places_name.replace('.xlsx', '').replace('.csv', '') + '-intersect-' + shape_file_dir + '.xlsx'
    new_places.to_excel(new_name, index=False)
    print('Output:', new_name)
    print('Time taken:', time.time() - start)


if __name__ == '__main__':
    main()
