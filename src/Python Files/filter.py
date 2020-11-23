import pandas as pd
import math
import argparse

'''
Input example:
Takes two spreadsheets, one of places (with latitude and longitude) 
and one of points of interest from which to draw the radius from
python <name_of_script> -p <places_spreadsheet> -i <poi_spreadsheet> -r <radius>
'''

'''
Output:
Spreadsheet containing only the locations inside the desired radius
'''


# Useful distance function for latitude and longitude, coor1 and coor2 are coordinates
def distance(coor1, coor2):
    r = 6371000
    lat1 = coor1[0]
    lng1 = coor1[1]
    lat2 = coor2[0]
    lng2 = coor2[1]
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    deltaphi = math.radians(lat2 - lat1)
    deltalambda = math.radians(lng2 - lng1)
    a = math.sin(deltaphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(deltalambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return c * r


# Filters a df for locations within a radius of a list of coordinates (coord)
# Has options to change the latitude and longitude columns of the df
def distance_filter(df, coord, radius, latitude='latitude', longitude='loingitude', inplace=False):
    drop_list = []
    radius = float(radius)
    for i in range(len(df)):
        place = (df['latitude'].iloc[i], df['longitude'].iloc[i])
        dist = 100000000
        for j in range(len(coord)):
            dist = min(dist, distance(place, coord[j]))
        if dist > radius:
            drop_list.append(i)
    if inplace:
        df = df.drop(drop_list, inplace=True)
        return None
    else:
        return df.drop(drop_list)


# Takes input if the file is executed on its own
def main():
    input = argparse.ArgumentParser()
    input.add_argument('-p', '--places_spreadsheet', required=True, help='Spreadsheet containing list of places and latitude/longitude')
    input.add_argument('-i', '--poi_spreadsheet', required=True, help='Spreadsheet containing list of points of interest')
    input.add_argument('-r', '--radius', required=True, help='Radius around points of interest')
    arguments = vars(input.parse_args())
    
    places_name = arguments['places_spreadsheet']
    int_name = arguments['poi_spreadsheet']
    radius = arguments['radius']
    
    if places_name[-4:] == 'xlsx':
        place_df = pd.read_excel(places_name,)
        x = 'xlsx'
    else:
        place_df = pd.read_csv(places_name)
        x = 'csv'
        
    if int_name[-4:] == 'xlsx':
        int_df = pd.read_excel(int_name)
    else:
        int_df = pd.read_csv(int_name)
    
    coord = list(zip(int_df['latitude'], int_df['longitude']))
    
    distance_filter(place_df, coord, radius, inplace=True)

    new_name = places_name[:-5] + '-filter_w-' + int_name[:-4] + '-' + str(radius) + 'm.xlsx'

    place_df.to_excel(new_name)
    print('Output:', new_name)
    

if __name__ == '__main__':
    main()
