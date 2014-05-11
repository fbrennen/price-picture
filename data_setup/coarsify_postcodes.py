#! /usr/bin/python

from pymongo import MongoClient
from bson import Code

from .. import db_schemas as schemas

# We've got very detailed postcode data, but are more interested in a larger
# scale for now, so we'll aggregate everything under the first bit of the
# postcode, and average the coordinates together.

def coarsify(input_collection, output_collection_name):
    """Averages together the GPS coordiantes for postcodes under a single prefix,
    and saves them to another collection.
    """
    # TODO: This map won't work properly for a few postcodes, such as those
    # with single-letter initial designators. Will work for OX* for now tho!
    themap = Code("function () {"
                  "  emit(this.postcode.substring(0,4).trim(),"
                  "       { lat:this.lat, long:this.long, count:1 });"
                  "}")
    thereduce = Code("function(key, values) {"
                     "  lattotal = 0;"
                     "  longtotal = 0;"
                     "  count = 0;" # So we can reduce multiple times per key
                     "  for(i in values) {"
                     "    lattotal += values[i].lat * values[i].count;"
                     "    longtotal += values[i].long * values[i].count;"
                     "    count += values[i].count;"
                     "  }"
                     "  return { 'lat': lattotal / count,"
                     "           'long': longtotal / count,"
                     "           'count': count };"
                     "}")
    input_collection.map_reduce(themap, thereduce, output_collection_name)
    
if __name__ == '__main__':
    client = MongoClient();
    database = client[schemas.db_name]
    collection = database[schemas.input_postcode_collection_name]
    output_collection_name = schemas.postcode_collection_name
    coarsify(collection, output_collection_name)
