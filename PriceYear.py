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

from collections import namedtuple
from datetime import datetime

from pymongo import MongoClient
from bson import Code

class PriceYear():
    """Aggregates postcode data for a single year, and compares them to the
    previous year. Provides an iterator to cycle through this year's data.

    Public methods:
    - __init__(year, collection, previous_PriceYear) -- generates the PriceYear.

    Public variables:
    - PostcodePrice -- a namedtuple of data for one postcode
    - postcode_map, price_reduce, median_finalize -- used to find data from the
      DB.
    - year -- the year this PriceYear corresponds to.
    - median_prices -- a dictionary mapping postcodes to PostcodePrices
    """

    PostcodePrice = namedtuple('PostcodePrice', ['postcode', 'median_price',
                                                     'pct_increase', 'year'])
    postcode_map = Code("function() {"
                        "  emit(this.postcode.substring(0,4).trim(),"
                        "       this.price);"
                        "}")
    price_reduce = Code("function(key, values) {"
                        "  result = {'prices': []};"
                        "  for(i in values) {"
                        "    if(values[i].prices) {"
                        "        result.prices = "
                        "            result.prices.concat(values[i].prices);"
                        "    } else {"
                        "        result.prices.push(values[i]);"
                        "    }"
                        "  }"
                        "  return result;"
                        "}")
    median_finalize = Code("function(key, reducedvalues) {"
                           "  if(!reducedvalues.prices) {"
                           "    return reducedvalues;"
                           "  }"
                           "  results = reducedvalues.prices;"
                           "  results.sort();"
                           "  numvals = results.length;"
                           "  if(numvals % 2 != 0) {"
                           "    return (results[(numvals + 1) / 2] + "
                           "            results[(numvals + 1) / 2 - 1]) / 2;"
                           "  }"
                           "  return results[numvals / 2];"
                           "}")
                        

    def __init__(self, year, collection, previous_PriceYear = None):
        """Constructor.

        Accepts the year of the data, a pymongo collection to pull the data
        from, and a PriceYear to compare this one to, in order to produce the
        percent difference between the two years. For the first year in a
        series, previous_PriceYear should be None.
        """
        self.year = year
        yearstart = datetime(int(year), 1, 1)
        yearend = datetime(int(year), 12, 31)
        results = collection.inline_map_reduce(self.postcode_map,
                                               self.price_reduce,
                                               finalize = self.median_finalize,
                                               query = {'date': {'$gte': yearstart,
                                                                 '$lte': yearend}})
        self.median_prices = {}
        for entry in results:
            pct_increase = 0
            if previous_PriceYear is not None:
                last_median = previous_PriceYear._get_median_for(entry['_id'])
                if last_median != 0:
                    pct_increase = entry['value'] / last_median
            self.median_prices[entry['_id']] = self.PostcodePrice(entry['_id'],
                                                                  entry['value'],
                                                                  pct_increase,
                                                                  year)
        self.__keys = self.median_prices.keys()
        self.__keys.sort()
            
    def _get_median_for(self, postcode):
        """Returns the median price for a postcode.

        Called by other PriceYears in order to generate percentage changes in
        price.
        """
        if postcode in self.median_prices:
            return self.median_prices[postcode].median_price
        return 0

    def __iter__(self):
        """These next two allow us to iterate through the PostcodePrices in the
        class.
        """
        self.__keyindex = 0
        return self

    def next(self):
        try:
            postcode_price = self.median_prices[
                self.__keys[self.__keyindex]]
        except IndexError:
            raise StopIteration
        self.__keyindex += 1
        return postcode_price
