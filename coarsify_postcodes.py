#! /usr/bin/python

from pymongo import MongoClient
from bson import Code

# We've got very detailed postcode data, but are more interested in a larger
# scale for now, so we'll aggregate everything under the first bit of the
# postcode, and average the coordinates together.

def coarsify(input_collection, output_collection_name):
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
    database = client['price_picture']
    collection = database['postcodes']
    output_collection_name = 'postcode_prefix'
    coarsify(collection, output_collection_name)
