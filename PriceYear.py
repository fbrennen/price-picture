#! /usr/bin/python

from pymongo import MongoClient
from collections import namedtuple
from datetime import datetime
from bson import Code

class PriceYear():
    """
    Aggregates postcode data for a single year, and compares them to the
    previous year. Provides an iterator to cycle through this year's data.

    Input:
    - An instance of PriceYear for the previous year, or None for the
      first year in the series.
    - The year.
    - A db collection to extract data from.
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
                last_median = previous_PriceYear.get_median_for(entry['_id'])
                if last_median != 0:
                    pct_increase = entry['value'] / last_median
            self.median_prices[entry['_id']] = self.PostcodePrice(entry['_id'],
                                                                  entry['value'],
                                                                  pct_increase,
                                                                  year)
        self.__keys = self.median_prices.keys()
        self.__keys.sort()
            
    def get_median_for(self, postcode):
        if postcode in self.median_prices:
            return self.median_prices[postcode].median_price
        return 0

    def __iter__(self):
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
