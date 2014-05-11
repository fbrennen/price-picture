#! /usr/bin/python

"""
db_schemas.py

Names of the databases and collections used for storing price_picture data.
This should probably be expanded, as there are still several collection-specific
accessors in MapDisplay and PriceYear.
"""

db_name = 'price_picture'
prices_collection_name = 'prices'
input_postcode_collection_name = 'postcodes'
postcode_collection_name = 'postcode_prefix'
