#! /usr/bin/python

import cPickle
import os.path
from collections import namedtuple

import matplotlib.pyplot as plotter
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colorbar import ColorbarBase
from matplotlib.animation import FuncAnimation
from mpl_toolkits.basemap import Basemap
from pymongo import MongoClient

import db_schemas as schemas
from PriceYear import PriceYear

pickle_filename = 'highresmap.pickle'

class MapDisplay():
    """Collect historical data and animate the results.

    This makes the magic happen. It pulls together PriceYears for the requested
    range, renders a map, and animates the difference from one PriceYear to the
    next.

    At the moment we've only got data for Oxfordshire, and the only supported
    animation is of the percentage difference in median price between a given year
    and 1996.

    Before this class can be used it's necessary to assemble the price data and
    bung it in a MongoDB instance. See the import_* and coarsify_* modules.

    Public methods:
    __init__(startyear, endyear) -- assembles our data.
    display_median_price_information() -- animates everything.
    """

    # These have the lat-lon reversed from the way Basemap wants them because of
    # copy-paste from Google Maps. =) 
    landmarks = { 'Oxford': ( 51.7504163, -1.2475879 ),
                  'Abingdon': ( 51.6743376, -1.2824895 ),
                  'Woodstock': ( 51.8541088, -1.3533688 ),
                  'Wallingford': ( 51.5975582, -1.1291238 ),
                  'Banbury': ( 52.0640782, -1.3386274 ),
                  'Chipping Norton': ( 51.9398064, -1.5519486 ),
                  'Thame': ( 51.7444865, -0.974216,15 ),
                  'Witney': ( 51.7863378, -1.4952446 ),
                  'Wantage': ( 51.5872542, -1.4248881 ),
                  'Didcot': ( 51.6093045, -1.2431861 ),
                  'Bicester': ( 51.9053114, -1.1543568 ) }

    """
    We want colors for both percentage increases and decreses in median price,
    so we'll use [0, 0.2] for decreases and [0.2, 1.0] for increases. It will
    probably look slightly messy when it hits 0.2 =)
    """
    color_scale = { 'red': [(0.0, 0.0, 0.0),
                            (0.2, 0.0, 1.0),
                            (1.0, 1.0, 0.0)],
                    'green': [(0.0, 0.0, 0.0),
                              (0.2, 0.0, 0.7),
                              (0.8, 0.0, 0.0),
                              (1.0, 0.0, 0.0)],
                    'blue': [(0.0, 0.0, 1.0),
                             (0.2, 0.2, 0.0),
                             (1.0, 0.0, 0.0)],
                    'alpha': [(0.0, 0.0, 0.8),
                              (0.2, 0.5, 0.5),
                              (1.0, 0.9, 0.0)]} 
                    
    def __init__(self, startyear, endyear):
        """Constructor.

        Inputs are a startyear and an endyear, which must both exist in the
        price information DB.

        An additional requirement is an active local MongoDB instance, which
        we'll use to pull price data and postcode data out of.

        A full-resolution Basemap instance is used so that we can get pretty
        rivers. This is quick to load once it's been pickled (see the functions
        at the end of the module), but if the map doesn't exist there will be a
        one-time delay while it's built.
        """
        if (not os.path.isfile(pickle_filename)):
            print 'No pickled map found! Creating one.'
            prepare_highres_data()
        self.themap = cPickle.load(open(pickle_filename, 'rb'))
        self.startyear = startyear
        self.endyear = endyear

        try:
            client = MongoClient()
        except ConnectionFailure:
            print "Can't connect to mongoDB -- is it running?"
            return False
        db = client[schemas.db_name]
        self._load_postcodes(db[schemas.postcode_collection_name])
        self._prepare_price_data(startyear,
                                 endyear,
                                 db[schemas.prices_collection_name])
        self._colormap = LinearSegmentedColormap('price_colors',
                                                MapDisplay.color_scale)

    def display_median_price_animation(self):
        """Kicks off the animation of median price information."""
        fig = plotter.figure(num = 1, figsize = (10, 12), tight_layout = True)
        fig.canvas.set_window_title('Percent increase in median house ' + \
                                    'price since 1996')

        axis = fig.add_axes([0.85, 0.04, 0.03, 0.92])
        colorbar_ticks = [0, .2, .4, .6, .8, 1.0]
        colorbar_labels = ['-100%', '0%', '250%', '500%', '750%', '>1000%']
        colorbar = ColorbarBase(axis, self._colormap, orientation='vertical')
        colorbar.set_ticks(colorbar_ticks)
        colorbar.set_ticklabels(colorbar_labels)

        fig.add_axes([0.0, 0.0, 0.82, 1.0])
        anim = FuncAnimation(fig,
                             self._animate,
                             frames = self.endyear + 1 - self.startyear,
                             interval = 1000,
                             blit = True,
                             init_func = self._init_animate,
                             repeat_delay = 3000)
        fig.show()

    def _init_animate(self):
        """Initializes background drawings for the animation."""
         return self._draw_background_data()

    def _animate(self, frame):
        """Draws a single price year as part of the animation."""
        year_index = frame % (self.endyear + 1 - self.startyear)
        return self._display_price_year(self.price_data[year_index])
        
    def _load_postcodes(self, collection):
        """Loads postcode prefixes and their GPS coordinates from the DB."""
        print "Loading postcode locations."
        Coordinate = namedtuple('Coordinate', ['lon', 'lat'])
        self.postcodes = {}
        for entry in collection.find():
            postcode = entry['_id']
            lat = entry['value']['lat']
            lon = entry['value']['long']
            self.postcodes[postcode] = Coordinate(lon, lat)

    def _prepare_price_data(self, startyear, endyear, collection):
        """Grabs price data from the DB and assembles our collection of
        PriceYears.
        """
        print "Generating median price data."
        try:
            self.base_year = PriceYear(startyear, collection)
        except OperationFailure:
            print "Can't find the prices collection!"
            return False
        self.price_data = [self.base_year]
        for year in range(startyear + 1, endyear + 1):
            self.price_data.append(PriceYear(year, collection, self.base_year))

    def _display_price_year(self, priceyear):
        """Renders data for a single PriceYear.

        Returns an iterable of the drawn objects so we can use blit animation.
        """
        drawn_stuff = []
        for postcode in priceyear:
            normalization = self._normalize_pct_increase(postcode.pct_increase)
            try:
                lon, lat = self.postcodes[postcode.postcode]
                # There are a few nonexistant postcodes in the records, e.g. OX6.
                # I'm guessing these were remapped in the past for whatever reason.
            except KeyError:
                continue
            x, y = self.themap(lon, lat)
            drawn_stuff += plotter.plot(x,
                                        y,
                                        'o',
                                        color = self._colormap(normalization),
                                        markersize = 70 * normalization + 10)
        return tuple(drawn_stuff) + (plotter.text(500, 500, str(priceyear.year)),)
        
    def _normalize_pct_increase(self, pct_increase):
        """Maps a percentage change to [0,1]

        Input percentage changes will range from 0 upwards.
    
        We'll cap our percent increases at 1000% for now, which should give us a
        decent range. We could let increases greater than that fall outsize
        [0,1] and the colormap would still be happy, but if we cap them properly
        we can also scale marker sizes. 

        These aren't really "percentage increases", but rather "percent of the
        previous median value", so an increase of 20% will be 1.2, and a
        decrease 0.8. 
        """        
        if pct_increase > 1:
            normalized = (pct_increase - 1) * 0.8 / 10 + 0.2
            if normalized > 1: 
                normalized = 1.0
            return normalized
        else:
            return (pct_increase - 1) * 0.2 + 0.2
        
    def _draw_background_data(self):
        """Draws the fixed data in the plot, e.g. landmarks and rivers.

        Returns the drawn items so we can use blit animation.
        """
        drawn_stuff = []
        self.themap.drawrivers()

        for city in MapDisplay.landmarks:
            x, y = self.themap(MapDisplay.landmarks[city][1],
                               MapDisplay.landmarks[city][0])
            drawn_stuff += self.themap.plot(x, y, 'ko')
            plotter.text(x + 500, y + 500, city)
        return tuple(drawn_stuff)

def prepare_highres_data():
    """Generated high-resolution data and pickles it.

    Highres data takes a long time to prepare but is worth the effort, so
    we'll pickle it!
    """
    print 'Preparing highres data, give us a few minutes.'
    themap = get_highres_map()
    cPickle.dump(themap, open(pickle_filename, 'wb'), -1)

def get_highres_map():
    """Specifies the format of the high-resolution Basemap."""
    return Basemap(llcrnrlat = 51.462371, llcrnrlon = -1.726692,
                   urcrnrlat = 52.187215, urcrnrlon = -0.836800,
                   resolution = 'f', projection = 'tmerc',
                   lat_0 = 51.874893, lon_0 = -1.281746, area_thresh = 1)
        
