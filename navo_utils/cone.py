from IPython.core.debugger import Tracer
from astroquery.query import BaseQuery
import html # to unescape, which shouldn't be neccessary but currently is
from .registry import Registry
from . import utils
from astropy.table import Table, vstack
import requests, io, astropy


class ConeClass(BaseQuery):
    def __init__(self):
        super(ConeClass, self).__init__()

    def query(self, incoords, inradius, services=None, max_services=10, **kwargs):


        if type(inradius) is float or type(inradius) is int or type(inradius) is str:
            inradius=[inradius]
        elif len(inradius) > 1:
            assert len(inradius) == len(incoords), "Please give either a single radius or one for each input position."
            
        #Tracer()()
        # Get the list of URLs that provide matching cone searches 
        #
        if services is None: 
            try:
                services=Registry.query(service_type='cone',**kwargs)
            except:
                raise 
        elif type(services) is astropy.table.row.Row:
            # The user handed one row of an astropy table, e.g., from
            # a registry query, make it look like a list
            services=[services] 
        elif type(services) is str:
            services=[{'access_url':services}]
        else:
            #? 
            pass 

        if len(services) > max_services:
            print("WARNING: You're asking to query more than {} services; I'm only going to do the first {}. If you really mean it, then set the max_services parameter to a larger number than that.".format(len(services),max_services))
            

        coords=utils.parse_coords(incoords,**kwargs)

        # For now, a list of tables, one table per service:
        all_results=[]
        # If there's more than one service URL found, then loop
        print("Found {} services to query.".format(len(services)))
        for i,service in enumerate(services):
            if i>=max_services: break
            print("    Querying service {}".format(html.unescape(service['access_url'])))
            # Initialize a cone table to add results to:
            service_results=self._astropy_cone_table_from_votable_response('')
            for i,c in enumerate(coords):
 
                if len(inradius) > 1: 
                    radius=inradius[i]
                elif type(inradius) is list:
                    radius=inradius[0]
                else:
                    radius=inradius
                result=self._one_cone_search(c.ra.deg,c.dec.deg,radius,html.unescape(service['access_url']))
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
        #response=self._request('GET',service,params=params,cache=False)
        response=self._request('POST',service,data=params,cache=False)
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

