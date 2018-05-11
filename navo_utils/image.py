from IPython.core.debugger import Tracer
from astroquery.query import BaseQuery
from astroquery.utils import parse_coordinates
from astropy.coordinates import SkyCoord
import html # to unescape, which shouldn't be neccessary but currently is
from . registry import Registry
from . import utils
from astropy.table import Table, vstack
import requests, io, astropy 
import urllib.request
from astropy.utils.data import download_file


class ImageClass(BaseQuery):
    def __init__(self):
        super(ImageClass, self).__init__()
        self._TIMEOUT=3 # seconds to timeout
        self._RETRIES = 3 # total number of times to try

    def query(self, coords, service, inradius='0.000001'):
        """Basic image search query function 

        Input coords should be either a single string, a single
        SkyCoord object, or a list. It will then loop over the objects
        in the list, assuming each is a single source. Within the
        _one_image_search function, it then expects likewise a single
        string, a single SkyCoord object, or list of 2 as an RA,DEC
        pair.

        Input service can be a string URL, an astropy Table returned
        from Registry.query() (or selected from it), or a single row
        of an astropy Table. If none is given, the kwargs will be
        passed to a Registry.query() call. 

        """
        if type(service) is str:
            service={"access_url":service}
        
        if type(coords) is str or isinstance(coords,SkyCoord):
            coords=[coords]
        assert type(coords) is list, "ERROR: Give a coordinate object that is a single string, a list/tuple (ra,dec), a SkyCoord, or a list of any of the above."
#        Tracer()()
        if type(inradius) is not list:
            radius =  [inradius]*len(coords)
        else:
            radius = inradius            
            assert len(radius) == len(coords), 'Please give either single radius or list of radii of same length as coords.'

        # Construct list of dictionaries, each with the parameters needed 
        # for the function you're calling in the query_loop:
        params=[{'coords':c,'radius':radius[i]} for i,c in enumerate(coords)] 
        return utils.query_loop(self._one_image_search, service=service, params=params)
        
    def _one_image_search(self, coords, radius, service):
        if ( type(coords) is tuple or type(coords) is list) and len(coords) == 2:
            coords=parse_coordinates("{} {}".format(coords[0],coords[1]))
        elif type(coords) is str:
            coords=parse_coordinates(coords)
        else:
            assert isinstance(coords,SkyCoord), "ERROR: cannot parse input coordinates {}".format(coords)

        #params = {'RA': coords.ra.deg, 'DEC': coords.dec.deg, 'SR':radius}
        params = {
            'POS': utils.sval(coords.ra.deg) + ',' + utils.sval(coords.dec.deg),
            'SIZE': radius,
            'FORMAT': 'ALL' #image_formats
        }
        response=utils.try_query(service,get_params=params,timeout=self._TIMEOUT,retries=self._RETRIES)
        return utils.astropy_table_from_votable_response(response)



### ---------------------------------------------- 
###################  WORK IN PROGRESS  #################
    def get(self, image_ref , filename='', row_ind=0):
        """Returns the data that can be handed to plt.imshow() from a URL
    
        TO DO: 

        * Write loop to handle list of urls, either list of row_ind or list of image_refs
        """
        
        col=utils.find_column_by_ucd(image_ref, 'VOX:Image_AccessReference')
        image_url=col[row_ind]
        
        if filename is '':
            filename='tmp.fits'
        self._download( image_url, filename=filename)
        if filename == 'tmp.fits':
            hdus=astropy.io.fits.open('tmp.fits')
            # Which extension? TBD
            return hdus[0].data
        else:
            print('Downloaded file. Saved as '+filename)
            return

    def _download(self, url, filename=''):
        # simple wrapper of urllib
        urllib.request.urlretrieve(url, filename=filename)
        return
######### End: WORK IN PROGRESS ###
Image=ImageClass()