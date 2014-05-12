#! /usr/bin/python

""" Copyright 2014 Forrest Brennen

    This file is part of price_picture.

    price_picture is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    price_picture is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with price_picture.  If not, see <http://www.gnu.org/licenses/>.
"""

import csv
from sys import argv, exit

from pymongo import MongoClient, errors

from .. import db_schemas as schemas

"""
import_postcodes.py

This processes a list of full postcodes and dumps them into a DB. You'll want
to call coarsify_postcodes after this to merge them together.

The Ordinance Survey only provides postcodes in grid-reference Northings and
Eastings and we'd rather like GPS coordinates. Luckily they also provide a tool
to convert those to a more useful format, called Grid InQuest, which you can
find here:

http://www.ordnancesurvey.co.uk/business-and-government/help-and-support/navigation-technology/os-net/grid-inquest.html 

Sadly, that just gives us postcodes in degrees, minutes, and seconds, and
we need them in decimal degrees (for sanity, and also for Basemap), so we'll
convert them to that format as well.
"""

postcode_fieldnames = ('postcode', 'latdeg', 'latmin', 'latsec', 'latdir',
                       'longdeg', 'longmin', 'longsec', 'longdir')

def dms_to_dd(degrees, minutes, seconds, direction):
    """Converts from degrees, minutes, seconds to decimal degrees."""
    dir_modifier = 1
    if direction == 'S' or direction == 'W':
        dir_modifier = -1
    return dir_modifier * (float(degrees) + float(minutes) / 60 +
                           float(seconds) / 3600)

def import_postcodes(collection, csv_file):
    """Imports postcodes from a csv_file, and saves them to a DB collection."""
    
    # Because this might take a while...
    lines = sum(1 for line in open(csv_file))
    line = 1;

    # Avoid duplicates
    collection.ensure_index('postcode', unique = True, drop_dups = True)
    
    with open(csv_file, 'rb') as csv_input:
        reader = csv.DictReader(csv_input, delimiter = ',',
                                fieldnames = postcode_fieldnames,
                                restval = 'unknown')
        for row in reader:
            print "\rProcessing line " + str(line) + " of " + str(lines),
            line += 1
            try:
                entry = { 'postcode': row['postcode'],
                          'lat': dms_to_dd(row['latdeg'], row['latmin'],
                                           row['latsec'], row['latdir']),
                          'long': dms_to_dd(row['longdeg'], row['longmin'],
                                            row['longsec'], row['longdir']) }
                collection.insert(entry)
            except ValueError:
                print 'Error parsing row:'
                print row
            except errors.DuplicateKeyError:
                pass

if __name__ == '__main__':
    if len(argv) < 2:
        print 'Give us a csv file!'
        exit()
    if not argv[1].endswith('.csv'):
        print 'Argument must be a .csv file'
        exit()
    client = MongoClient()
    database = client[schemas.db_name]
    collection = database[schemas.input_postcode_collection_name]
    import_postcodes(collection, argv[1])
