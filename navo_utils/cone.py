from IPython.core.debugger import Tracer
from astroquery.query import BaseQuery
import html # to unescape, which shouldn't be neccessary but currently is
from .registry import Registry
from . import utils
from astropy.table import Table, vstack
import requests, io, astropy
from astropy.coordinates import SkyCoord, ICRS

class ConeClass(BaseQuery):
    def __init__(self):
        super(ConeClass, self).__init__()

    def query(self, incoords, inradius, services=None, **kwargs):

        # Get the list of URLs that provide matching cone searches 
        if services is None: 
            try:
                services=Registry.query(service_type='cone',**kwargs)
                check=True
            except:
                raise 
        else: check=False

        # For now, a list of tables, one table per service:
        all_results=[]
        # If there's more than one service URL found, then loop
        print("Found {} services to query.".format(len(services)))

        for service in services:

            print("    Querying service {}".format(html.unescape(service['access_url'])))

            # Initialize a cone table to add results to:
            service_results=self._astropy_cone_table_from_votable_response('')

            for i,c in enumerate(incoords):
                #Tracer()() 
                # Doesn't like me to specify ICRS, though it works in debugger
                coords=SkyCoord(c,unit='deg')

                if len(inradius) > 1: 
                    radius=inradius[i]
                else:
                    radius=inradius
                

                result=self._one_cone_search(coords.ra.deg,coords.dec.deg,radius,html.unescape(service['access_url']))
                # Need a test that we got something back. Shouldn't error if not, just be empty
                if len(result) > 0:
                    # Extend requires that all the columns be the same. 
                    # (The meta data for the result columns are lost because assumed to be the same.)
                    # The "cone_table_from_votable" should do that but for now, append to a list.
                    print("    Got {} results for source number {}".format(len(result),i))
                    #Tracer()() 
                    service_results=vstack([service_results,result])
                else:
                    print("    (Got no results for source number {})".format(i))
            #Tracer()()
            if len(service_results) > 0:
                all_results.append(service_results)

        return all_results

    def _one_cone_search(self, ra, dec, radius, service):
        params = {'RA': ra, 'DEC': dec, 'SR':radius}
        # Currently using a GET not a post so that I can debug it by copy-pasting the URL in a browser
        #Tracer()()
        response=self._request('GET',service,params=params)
        #response=self._request('POST',service,data=params)
        return self._astropy_cone_table_from_votable_response(response)

    def _astropy_cone_table_from_votable_response(self,response):
        """Need one of these for each class, or one generic standardize()? 
        
        For now, just simple conversion. Store the raw XML
        from the query as well as the URL in the meta data.
        In future, standardize the columns by replacing the 
        column name with the UCD if there is one.
        """
        #Tracer()()
        try:
            table= Table.read(io.BytesIO(response.content))
            # Store the raw response content and the url queried
            #  in the meta data of the table. Make its value a list,
            #  because this will allow us to concatenate (vstack)
            #  different queries and merge the metadata
            table.meta['xml_raw']=[response.content]
            table.meta['url']=[response.url]
            return table
        except:
            empty=Table(masked=True)
            empty.meta['xml_raw']=[]
            empty.meta['url']=[]
            return empty

Cone=ConeClass()

