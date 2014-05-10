#! /usr/bin/python

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plotter
import cPickle
import os.path

pickle_filename = 'highresmap.pickle'

class MapDisplay():

    landmarks = { 'Oxford': ( 51.7504163, -1.2475879 ),
                  'Abingdon': ( 51.6743376, -1.2824895 ),
                  'Woodstock': ( 51.8541088, -1.3533688 ),
                  'Wallingford': ( 51.5975582, -1.1291238 ),
                  'Faringdon': ( 51.6533383, -1.5850389 ),
                  'Banbury': ( 52.0640782, -1.3386274 ),
                  'Chipping Norton': ( 51.9398064, -1.5519486 ) }
    
    def __init__(self):
        if (not os.path.isfile(pickle_filename)):
            print 'No pickled map found! Creating one.'
            prepare_highres_data()
        self.themap = cPickle.load(open(pickle_filename, 'rb'))
        self.themap.drawrivers()

        for city in MapDisplay.landmarks:
            x, y = self.themap(MapDisplay.landmarks[city][1],
                               MapDisplay.landmarks[city][0])
            self.themap.plot(x, y, 'bo')
            plotter.text(x + 500, y + 500, city)
        plotter.show()

"""
Highres data takes a long time to prepare but is worth the effort, so
we'll pickle it!
"""
def prepare_highres_data():
    print 'Preparing highres data, give us a few minutes.'
    themap = get_highres_map()
    cPickle.dump(themap, open(pickle_filename, 'wb'), -1)

def get_highres_map():
    return Basemap(llcrnrlat = 51.462371, llcrnrlon = -1.726692,
                   urcrnrlat = 52.187215, urcrnrlon = -0.836800,
                   resolution = 'f', projection = 'tmerc',
                   lat_0 = 51.874893, lon_0 = -1.281746, area_thresh = 1)
        
