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
