#! /usr/bin/python

from pymongo import MongoClient, errors
import csv
from sys import argv, exit

postcode_fieldnames = ('postcode', 'latdeg', 'latmin', 'latsec', 'latdir',
                       'longdeg', 'longmin', 'longsec', 'longdir')

# Our inputs are in degrees, minutes, and seconds, and we'd like decimals
def dms_to_dd(degrees, minutes, seconds, direction):
    dir_modifier = 1
    if direction == 'S' or direction == 'W':
        dir_modifier = -1
    return dir_modifier * (float(degrees) + float(minutes) / 60 + float(seconds) / 3600)

def import_postcodes(collection, csv_file):
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
    database = client['price_picture']
    collection = database['postcodes']
    import_postcodes(collection, argv[1])
