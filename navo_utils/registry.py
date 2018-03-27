# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VO Queries
"""

from __future__ import print_function, division

import warnings
import json
import time
import os
import re
#import keyring
import io
from . import utils

import numpy as np

from requests import HTTPError
from getpass import getpass
from base64 import b64encode

import astropy.units as u
import astropy.coordinates as coord

from astropy.table import Table, Row, vstack, MaskedColumn
from astropy.extern.six.moves.urllib.parse import quote as urlencode
from astropy.extern.six.moves.http_cookiejar import Cookie
from astropy.utils.exceptions import AstropyWarning
from astropy.logger import log

from astroquery.query import BaseQuery
from astroquery.utils import commons, async_to_sync
from astroquery.utils.class_or_instance import class_or_instance
from astroquery.exceptions import (TimeoutError, InvalidQueryError, RemoteServiceError,
                          LoginError, ResolverError, MaxResultsWarning,
                          NoResultsWarning, InputWarning, AuthenticationWarning)


__all__ = ['Registry', 'RegistryClass']


class RegistryClass(BaseQuery):
    """
    Registry query class.
"""


    def __init__(self):

        super(RegistryClass, self).__init__()

        self._REGISTRY_TAP_SYNC_URL = "https://vao.stsci.edu/RegTAP/TapService.aspx/sync"

    def query(self, **kwargs):
        
        
        adql = self._build_adql(**kwargs)
        x = """
            select b.waveband,b.short_name,a.ivoid,b.res_description,c.access_url,b.reference_url from rr.capability a 
            natural join rr.resource b 
            natural join rr.interface c
            where a.cap_type='SimpleImageAccess' and a.ivoid like 'ivo://%stsci%' 
            order by short_name
        """
        if 'debug' in kwargs and kwargs['debug']==True: print ('Registry:  sending query ADQL = {}\n'.format(adql))

        if 'method' in kwargs:
            method = kewargs['method']
        else:
            method = 'POST'

        url = self._REGISTRY_TAP_SYNC_URL
        
        tap_params = {
            "request": "doQuery",
            "lang": "ADQL",
            "query": adql
        }
        
        response = self._request(method, url, data=tap_params)
        
        if 'debug' in kwargs and kwargs['debug']==True: print('Queried: {}\n'.format(response.url))
        
        aptable = utils.astropy_table_from_votable_response(response)
        
        return aptable
    
    def _build_adql(self, **kwargs):
        
        # Default values
        service_type=""
        keyword=""
        waveband=""
        source=""
        order_by=""
        logic_string=" and "
        
        # Find the keywords we recognize
        for key,val in kwargs.items():
            if (key == 'service_type'):
                service_type = val
            elif (key == 'keyword'):
                keyword = val
            elif (key == 'waveband'):
                waveband = val
            elif (key == 'source'):
                source = val
            elif (key == 'order_by'):
                order_by = val
            elif (key == 'logic_string'):
                logic_string = val
        
        ##
        if "image" in service_type.lower():
            service_type="simpleimageaccess"
        elif "spectr" in service_type.lower():
            service_type="simplespectralaccess"
        elif "cone" in service_type.lower():
            service_type="conesearch"
        else:
            service_type="tableaccess"
    
        query_retcols="""
          select res.waveband,res.short_name,cap.ivoid,res.res_description,
          int.access_url, res.reference_url
           from rr.capability cap
           natural join rr.resource res
           natural join rr.interface int
           """
        
        x = """
            select b.waveband,b.short_name,a.ivoid,b.res_description,c.access_url,b.reference_url from rr.capability a 
    natural join rr.resource b 
    natural join rr.interface c
        """
        query_where="where "
        
        wheres=[]
        if service_type is not "":
            wheres.append("cap.cap_type='{}'".format(service_type))
        if source is not "":
            wheres.append("cap.ivoid like '%{}%'".format(source))
        if waveband is not "":
            wheres.append("res.waveband like '%{}%'".format(waveband))
        if (keyword is not ""):
            keyword_where = """
             (res.res_description like '%{}%' or
            res.res_title like '%{}%' or
            cap.ivoid like '%{}%') 
            """.format(keyword, keyword, keyword)
            wheres.append(keyword_where)
        
        query_where=query_where+logic_string.join(wheres)
        
        if order_by is not "":
            query_order="order by {}".format(order_by)
        else: query_order=""
        
        query=query_retcols+query_where+query_order
        
        return query


Registry = RegistryClass()




def display_results(results):
    # Display results in a readable way including the 
    # short_name, ivoid, res_description and reference_url.

    for row in results:
        md = f'{row["short_name"]} ({row["ivoid"]})'
        print(md)
        print (row['res_description'])
        print (f'(More info: {row["reference_url"]} )')

def main():
    results = Registry.query(source='nasa.heasarc', service_type='image')
    
    display_results(results)    
    


#
# Main program
#
    
if __name__ == "__main__":
    import sys
    #fib(int(sys.argv[1]))
    main()
    
