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
from enum import Enum

__all__ = ['Spectra', 'SpectraClass']

class SpectraClass(BaseQuery):
    def __init__(self):
        super(SpectraClass, self).__init__()
        self._TIMEOUT=30 # seconds to timeout
        self._RETRIES = 3 # total number of times to try


    def query(self, service, coords, radius='0.000001', image_format=None, verbose=False):
        """Basic spectra search query function 

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
        if type(radius) is not list:
            inradius =  [radius]*len(coords)
        else:
            inradius = radius            
            assert len(inradius) == len(coords), 'Please give either single radius or list of radii of same length as coords.'
        # Passing along proper image format parameters:
        if image_format is not None:
            if "fits" in image_format.lower():
                image_format="image/fits"
            elif "jpeg" in image_format.lower():
                image_format="image/jpeg"
            elif "jpg" in image_format.lower():
                image_format="image/jpeg"
            elif "png" in image_format.lower():
                image_format="image/png"
            elif "graphics" in image_format.lower():
                image_format="GRAPHICS"
            elif "all" in image_format.lower():
                image_format="ALL"
            else:
                raise Exception("ERROR: please give a image_format that is one of FITS, JPEG, PNG, ALL, or GRAPHICS")

        # Expand the input parameters to a list of input parameter dictionaries for the call to query_loop.
        params=[{'coords':c,'radius':inradius[i], 'image_format':image_format} for i,c in enumerate(coords)] 
        
        return utils.query_loop(self._one_image_search, service=service, params=params, verbose=verbose)
        
    def _one_image_search(self, coords, radius, service, image_format=None):
        if ( type(coords) is tuple or type(coords) is list) and len(coords) == 2:
            coords=parse_coordinates("{} {}".format(coords[0],coords[1]))
        elif type(coords) is str:
            coords=parse_coordinates(coords)
        else:
            assert isinstance(coords,SkyCoord), "ERROR: cannot parse input coordinates {}".format(coords)

        params = {
            'POS': utils.sval(coords.ra.deg) + ',' + utils.sval(coords.dec.deg),
            'SIZE': utils.sval(2.*float(radius)),   #Note: size in SIA is diameter, not radius!
            }
        if (image_format is not None):
            params['FORMAT'] = image_format
            
        response=utils.try_query(service, get_params=params, timeout=self._TIMEOUT, retries=self._RETRIES)
        return utils.astropy_table_from_votable_response(response)
    
    def get_column(self, table, mnemonic):
        col = None
        if not isinstance(mnemonic, SpectraColumn):
            raise ValueError('mnemonic must be an enumeration member of SpectraColumn.')
        elif not isinstance(table, Table):
            raise ValueError('table must be an instance of astropy.Table.')
        else:
            col = utils.find_column_by_utype(table, mnemonic.value)
        return col
    
    def get_column_name(self, table, mnemonic):
        name = None
        col = self.get_column(table, mnemonic)
        if col is not None:
            name = col.name
        return name
            
    

Spectra=SpectraClass()

class SpectraColumn(Enum):
    # Required columns
    ACCESS_URL = 'ssa:Access.Reference'
    FORMAT = 'ssa:Access.Format'
    
    # "Should have" columns
    
    # WCS (also "should have")
    