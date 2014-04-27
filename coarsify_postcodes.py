#! /usr/bin/python

from pymongo import MongoClient
from bson import Code

# We've got very detailed postcode data, but are more interested in a larger
# scale for now, so we'll aggregate everything under the first bit of the
# postcode.

def coarsify(input_collection, output_collection_name):
    # TODO: This map won't work properly for a few postcodes, such as those
    # with single-letter initial designators. Fix that sucker.
    themap = Code("function () {"
                  "  emit(this.postcode.substring(0,4).trim(),"
                  "       { lat:this.lat, long:this.long });"
                  "}")
    thereduce = Code("function(key, values) {"
                     "  lattotal = 0;"
                     "  longtotal = 0;"
                     "  for(i in values) {"
                     "    lattotal += values[i].lat;"
                     "    longtotal += values[i].long;"
                     "  }"
                     "  return { 'lat': lattotal / values.length,"
                     "           'long': longtotal / values.length };"
                     "}")
    input_collection.map_reduce(themap, thereduce, output_collection_name)
    
if __name__ == '__main__':
    client = MongoClient();
    database = client['price_picture']
    collection = database['postcodes']
    output_collection_name = 'postcode_prefix'
    coarsify(collection, output_collection_name)
