from IPython.core.debugger import Tracer
from astroquery.query import BaseQuery
import html # to unescape, which shouldn't be neccessary but currently is
from .registry import Registry
import utils

class ConeClass(BaseQuery):
    def __init__(self):
        super(ConeClass, self).__init__()

    def query(self, inra, indec, inradius, **kwargs):
        # Get the list of URLs that provide matching cone searches 
        services=Registry.query(service_type='cone',**kwargs)
        # For now, a list of tables, one table per service:
        all_results=[]
        # If there's more than one service URL found, then loop
        print("Found {} services to query.".format(len(services)))
        for service in services:
            print("    Querying service {}".format(html.unescape(service['access_url'])))
            # Initialize a cone table to add results to:
            service_results=astropy_cone_table_from_votable_response('')
            #  TO BE FIXED: should work if inra is a single float *or* string:
            for i,ra in enumerate(inra):
                # Construct params ... For now, hard wire:
                dec=indec[i]
                if len(inradius) > 1: 
                    radius=inradius[i]
                else:
                    radius=inradius
                result=self._one_cone_search(ra,dec,radius,html.unescape(service['access_url']))
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
        # For some reason, this has to be a GET not a POST?
        response=self._request('GET',service,params=params)
        return astropy_cone_table_from_votable_response(response)
    

Cone=ConeClass()

