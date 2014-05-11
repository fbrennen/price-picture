#! /usr/bin/python

import datetime
import csv
from dateutil.parser import parse
from sys import argv, exit

from pymongo import MongoClient, errors

from .. import db_schemas as schemas

"""
import_sale_data.py

The Land Registry gives us house prices in a very hefty and complicated format,
so we need to pull out just the appropriate bits and stuff them in a DB.
"""

# There are several additional fields here, but we only need the first four
sale_data_fieldnames = ('id', 'price', 'date', 'postcode')

def import_sale_data(collection, csv_file):
    """Pulls relevant data from a csv file and stuffs it into a DB collection."""
    # Because this might take a while...
    lines = sum(1 for line in open(csv_file))
    line = 1;

    # Avoid duplicates, and allow us to re-run imports
    collection.ensure_index('_id', unique = True, drop_dups = True)
    
    with open(csv_file, 'rb') as csv_input:
     
        reader = csv.DictReader(csv_input, delimiter = ',',
                                fieldnames = sale_data_fieldnames, 
                                restval = 'unknown')
        for row in reader:
            print "\rProcessing line " + str(line) + " of " + str(lines),
            line += 1
            try:
                # Temp hack to improve tractibility
                if not row['postcode'].startswith('OX'):
                    continue
                entry = { '_id': row['id'],
                          'date': parse(row['date']),
                          'price': int(row['price']),
                          'postcode': row['postcode'] }
                collection.insert(entry)
            except ValueError:
                print 'Error parsing date or price for row :'
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
    collection = database[schemas.prices_collection_name]
    import_sale_data(collection, argv[1])
    
