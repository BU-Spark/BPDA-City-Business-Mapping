"""
This function is a collection of loose functions
"""

import pandas as pd
import math
from shapely.geometry import Point
import geopandas as gpd
from ast import literal_eval

# Takes a pandas dataframe and default latitude and longitude names, then outputs 
# a geopandas dataframe
def create_gdp(df, latitude='latitude', longitude='longitude'):
    crs = {'init': 'epsg:4326'}
    geometry = [Point(xy) for xy in zip(df[longitude], df[latitude])]
    return gpd.GeoDataFrame(df.copy(), crs=crs, geometry=geometry)


# Compares distances between two coordinates in the latitude and lognitude coordinate system
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

# Given a desired radius in meters, this returns a value that can be used as a buffer 
# to plot that distance around points or shapes
# This function is unstable below 150m and does not accurately plot
def get_buffer(radius):
    count = 0
    thresh = .000001
    double = 0
    x_list = [0]

    co = [42.35, -71.13], [42.35, -71.1317]

    x = -71.1317

    while abs(distance([42.35, -71.13], [42.35, x]) - radius) > thresh:
        if distance([42.35, -71.13], [42.35, x]) - radius > thresh:
            x += 1/(100 * (count + 1))
            count += 1
            x = round(x, 6)
            x_list.append(x)
            if x_list[-1] == x_list[-2]:
                break

        elif distance([42.35, -71.13], [42.35, x]) - radius < thresh:
            x -= 1/(100 * (count + 1))
            count += 1
            x = round(x, 6)
            x_list.append(x)
            if x_list[-1] == x_list[-2]:
                break

    return round(abs(x - -71.13), 6)


# Compares numbers for addresses, determines if similar enough
# Some businesses don't have exact number addresses but are still the same business
def num_compare(num1, num2):
    if num1 == num2:
        return -1

    num1split = num1.split('-')
    num2split = num2.split('-')
    if len(num1split) > 1 and len(num2split) == 1:
        if num2 >= num1split[0] or num2 <= num1split[1]:
            return -1

    elif len(num2split) > 1 and len(num1split) == 1:
        if num1 >= num2split[0] or num1 <= num2split[1]:
            return -1

    elif len(num1split) == 1 and len(num2split) == 1:
        try:
            int(num1split[0])
            int(num2split[0])
            return abs(int(num1) - int(num2))
        except ValueError:
            return 100
    else:
        return 100


# Algorithm to compare names and output a True or False if they are similar enough
# NOT to be used on its own, only in conjunction with addresses
# (many businesses have similar names while not having the same address)
def name_compare(name1, name2):
    name1 = str(name1).lower().replace('\'', '').replace('-', '').replace('ctr', 'center')
    name2 = str(name2).lower().replace('\'', '').replace('-', '').replace('ctr', 'center')
    if name1 in name2 or name2 in name1:
        return -1
    else:
        count1 = 0
        count2 = 0
        for part1 in name1.split():
            if part1 in name2:
                count1 += 1
        for part2 in name2.split():
            if part2 in name1:
                count2 += 1
        score = (count2 + count1) / (len(name1.split()) + len(name2.split()))
        return score


# Given google data in the form of pandas data frame and a list of strings
# that are google types, this removes any entry that contain those types
def filter_google(goog, types):
    # type_filter_list = ['transit_station', 'park']
    type_filter_list = types
    type_filter_rows = []

    for i in range(len(goog)):
        i_list = literal_eval(goog.iloc[i]['types'])
        for type_filter in type_filter_list:
            if type_filter in i_list:
                type_filter_rows.append(i)

    goog.drop(type_filter_rows, inplace=True)
    if 'level_0' not in goog.columns:
        goog.reset_index(inplace=True, drop=True)

    return None


# Removes punctuation and replaces all long form street suffixes with
# the short form. Mainly for reducing addresses to compare them
def process_addr(addr):
    return addr.replace('.', '').replace(',', '').replace(
            'Street', 'St').replace('Avenue', 'Ave').replace(
            'Terrace', 'Ter').replace('Court', 'Ct').replace(
            'Road', 'Rd').replace(', Brighton', '').replace(
            ', Boston', '').replace(', Allston', '').replace(
            ', Brookline', '')


# Checks if a string has any numbers in it, used in compare_addr
def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)


# Compares addresses using a variety of functions written here
def compare_addr(addr1, addr2):
    addr1 = addr1.lower()
    addr2 = addr2.lower()
    l1 = addr1.split(' ')
    l2 = addr2.split(' ')
    if has_numbers(addr1) and has_numbers(addr2):
        score = num_compare(l1[0], l2[0])
        if score == -1 or score < 5:
            if l1[1] in l2[1] or l2[1] in l1[1]:
                if l1[2] in l2[2] or l2[2] in l1[2]:
                    return True
                
    else:
        if l1[0] in l2[0] or l2[0] in l1[0]:
            if l1[1] in l2[1] or l2[1] in l1[1]:
                return True
            
    return False

# Removes the pound sign and all after in an address to remove the unit number
# Mainly used for InfoUSA as unit numbers are not available with other data sources
def remove_unit(address):
    return address.split(' #')[0]


# This is an example of a large merge (4+ sources total)
# This should not be used on general data, but it is useful to see how it works
def merge21(ometh, nmeth):
    # Desired Columns for final dataframe
    cols = ['name', 
            'address', 
            'latitude', 
            'longitude', 
            'MSD Y/N', 
            'MSD Category', 
            'MSD Sub Category', 
            'New Method Y/N', 
            'Old Method Y/N', 
            'Google Y/N', 
            'Google Place ID', 
            'Google Types', 
            'Yelp Y/N', 
            'Yelp ID', 
            'Yelp Types', 
            'IUSA ID', 
            'IUSA Y/N',
            'IUSA Category'
           ]
    
    # Merge dictionary, can be converted to dataframe after merge
    md = {}
    
    for col in cols:
        md[col] = []
        
    ometh_m = set()
    nmeth_n = set()
    
    # The merge, n^2 that tracks what is seen to not repeat
    for i in range(len(ometh)):
        print((i*100)//len(ometh), '', end='')
        for j in range(len(nmeth)):
            if j not in nmeth_n:
                
                n1 = ometh.iloc[i]['Company Name']
                n2 = nmeth.iloc[j]['name']
                score = name_compare(n1, n2)

                a1 = remove_unit(process_addr(ometh.iloc[i]['Address']))
                a2 = process_addr(nmeth.iloc[j]['address'])

                # If it passes these, it is considered a match
                if (score == -1 or score > .6) and compare_addr(a1, a2):
                    md['name'].append(n2)
                    md['address'].append(nmeth.iloc[j]['address'])
                    md['latitude'].append(nmeth.iloc[j]['latitude'])
                    md['longitude'].append(nmeth.iloc[j]['longitude'])
                    md['MSD Category'].append(nmeth.iloc[j]['MSD Category'])
                    md['MSD Sub Category'].append(nmeth.iloc[j]['MSD Sub Category'])
                    md['Google Place ID'].append(nmeth.iloc[j]['Google Place ID'])
                    md['Google Types'].append(nmeth.iloc[j]['Google Types'])
                    md['Yelp ID'].append(nmeth.iloc[j]['Yelp ID'])
                    md['Yelp Types'].append(nmeth.iloc[j]['Yelp Types'])

                    md['New Method Y/N'].append('Y')
                    md['Old Method Y/N'].append('Y')
                    md['Google Y/N'].append('Y')

                    if type(nmeth.iloc[j]['MSD Category']) == str:
                        md['MSD Y/N'].append('Y')
                    else:
                        md['MSD Y/N'].append('N')

                    if type(nmeth.iloc[j]['Yelp Types']) == str:
                        md['Yelp Y/N'].append('Y')
                    else:
                        md['Yelp Y/N'].append('N')

                    md['IUSA ID'].append(ometh.iloc[i]['INFOUSA_ID'])
                    md['IUSA Y/N'].append('Y')
                    md['IUSA Category'].append(ometh.iloc[i]['Description'])
                    
                    ometh_m.add(i)
                    nmeth_n.add(j)
                
    # For anything not found a duplicate, adds the original record to our md
    for i in range(len(ometh)):
        if i not in ometh_m:
            n1 = ometh.iloc[i]['Company Name']
            md['name'].append(n1)
            md['address'].append(ometh.iloc[i]['Address'])
            md['latitude'].append(ometh.iloc[i]['Latitude'])
            md['longitude'].append(ometh.iloc[i]['Longitude'])
            md['MSD Category'].append('')
            md['MSD Sub Category'].append('')
            md['Google Place ID'].append('')
            md['Google Types'].append('')
            md['Yelp ID'].append('')
            md['Yelp Types'].append('')

            md['New Method Y/N'].append('N')
            md['Old Method Y/N'].append('N')
            md['Google Y/N'].append('N')
            md['MSD Y/N'].append('N')
            md['Yelp Y/N'].append('N')

            md['IUSA ID'].append(ometh.iloc[i]['INFOUSA_ID'])
            md['IUSA Y/N'].append('Y')
            md['IUSA Category'].append(ometh.iloc[i]['Description'])

    # Same for the other data source
    for j in range(len(nmeth)):
        if j not in nmeth_n:
            n2 = nmeth.iloc[j]['name']
            md['name'].append(n2)
            md['address'].append(nmeth.iloc[j]['address'])
            md['latitude'].append(nmeth.iloc[j]['latitude'])
            md['longitude'].append(nmeth.iloc[j]['longitude'])
            md['MSD Category'].append(nmeth.iloc[j]['MSD Category'])
            md['MSD Sub Category'].append(nmeth.iloc[j]['MSD Sub Category'])
            md['Google Place ID'].append(nmeth.iloc[j]['Google Place ID'])
            md['Google Types'].append(nmeth.iloc[j]['Google Types'])
            md['Yelp ID'].append(nmeth.iloc[j]['Yelp ID'])
            md['Yelp Types'].append(nmeth.iloc[j]['Yelp Types'])


            md['New Method Y/N'].append(nmeth.iloc[j]['New Method Y/N'])
            md['Old Method Y/N'].append(nmeth.iloc[j]['Old Method Y/N'])
            md['Google Y/N'].append(nmeth.iloc[j]['Google Y/N'])
            md['MSD Y/N'].append(nmeth.iloc[j]['MSD Y/N'])
            md['Yelp Y/N'].append(nmeth.iloc[j]['Yelp Y/N'])


            md['IUSA ID'].append('')
            md['IUSA Y/N'].append('N')
            md['IUSA Category'].append('')
    
    # returns the seen sets for convenience of analyzing the algorithm
    return md, ometh_m, nmeth_n

