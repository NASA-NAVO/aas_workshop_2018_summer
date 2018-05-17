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


class ImageClass(BaseQuery):
    def __init__(self):
        super(ImageClass, self).__init__()
        self._TIMEOUT=3 # seconds to timeout
        self._RETRIES = 3 # total number of times to try


    def query(self, service, coords, radius='0.000001', image_format=None):
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

        image_format = one of the following options: ALL, GRAPHICS, 
                    FITS, PNG, JPEG/JPG (default = ALL)

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
        # print(image_format)
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
                print("ERROR: please give a image_format that is one of FITS, JPEG, PNG, ALL, or GRAPHICS")
                return None


        # Expand the input parameters to a list of input parameter dictionaries for the call to query_loop.
        params=[{'coords':c,'radius':inradius[i], 'image_format':image_format} for i,c in enumerate(coords)] 
        
        return utils.query_loop(self._one_image_search, service=service, params=params)
        
    def _one_image_search(self, coords, radius, service, image_format=None):
        if ( type(coords) is tuple or type(coords) is list) and len(coords) == 2:
            coords=parse_coordinates("{} {}".format(coords[0],coords[1]))
        elif type(coords) is str:
            coords=parse_coordinates(coords)
        else:
            assert isinstance(coords,SkyCoord), "ERROR: cannot parse input coordinates {}".format(coords)

        #params = {'RA': coords.ra.deg, 'DEC': coords.dec.deg, 'SR':radius}
        params = {
            'POS': utils.sval(coords.ra.deg) + ',' + utils.sval(coords.dec.deg),
            'SIZE': utils.sval(2.*float(radius)),   #Note: size in SIA is diameter, not radius!
            }
        if (image_format is not None):
            params['FORMAT'] = image_format
            
        response=utils.try_query(service,get_params=params,
                timeout=self._TIMEOUT,retries=self._RETRIES)
        return utils.astropy_table_from_votable_response(response)


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
    
    def get_column_name(self, table, mnemonic):
        if not isinstance(mnemonic, ImageColumn):
            raise ValueError('mnemonic must be an enumeration member of ImageColumn.')
        elif not isinstance(table, Table):
            raise ValueError('table must be an instance of astropy.Table.')
        else:
            col = utils.find_column_by_ucd(table, mnemonic.value)
            if col is None:
                raise Exception(f'Column {mnemonic} (UCD {mnemonic.value}) not found in table.')
            else:
                name = col.name
                
        return name
            
    

Image=ImageClass()

class ImageColumn(Enum):
    # Required columns
    TITLE = 'VOX:Image_Title'
    RA = 'POS_EQ_RA_MAIN'
    DEC = 'POS_EQ_DEC_MAIN'
    NAXES = 'VOX:Image_Naxes'
    NAXIS = 'VOX:Image_Naxis'
    SCALE = 'VOX:Image_Scale'
    FORMAT = 'VOX:Image_Format'
    ACCESS_URL = 'VOX:Image_AccessReference'
    
    # "Should have" columns
    INSTRUMENT = 'INST_ID'
    MJD_OBS = 'VOX:Image_MJDateObs'
    REF_FRAME = 'VOX:STC_CoordRefFrame'
    BANDPASS = 'VOX:BandPass_ID'
    BANDPASS_UNIT = 'VOX:BandPass_Unit'
    BANDPASS_REFVAL = 'VOX:BandPass_RefValue'
    BANDPASS_HILIMIT = 'VOX:BandPass_HiLimit'
    BANDPASS_LOLIMIT = 'VOX:BandPass_LoLimit'
    PIXFLAGS = 'VOX:Image_PixFlags'
    FILESIZE = 'VOX:Image_FileSize'
    
    # WCS (also "should have")
    PROJECTION = 'VOX:WCS_CoordProjection'
    CRPIX = 'VOX:WCS_CoordRefPixel'
    CRVAL = 'VOX:WCS_CoordRefValue'
    CDMATRIX = 'VOX:WCS_CDMatrix'
    
    
from astroquery.mast import Observations
from astropy.utils.data import download_file