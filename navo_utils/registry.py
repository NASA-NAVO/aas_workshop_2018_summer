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
from astroquery import conf


__all__ = ['Registry', 'RegistryClass']

#
# Functions to help replace bytes with strings in astropy tables that came from VOTABLEs
#

def sval(val):
    """
    Returns a string value for the given object.  When the object is an instanceof bytes,
    utf-8 decoding is used.
    
    Parameters
    ----------
    val : object
        The object to convert
    
    Returns
    -------
    string
        The input value converted (if needed) to a string
    """
    if (isinstance(val, bytes)):
        return str(val, 'utf-8')
    else:
        return str(val)

# Create a version of sval() that operates on a whole column.
svalv = np.vectorize(sval)

def sval_whole_column(single_column):
    """
    Returns a new column whose values are the string versions of the values
    in the input column.  The new column also keeps the metadata from the input column.
    
    Parameters
    ----------
    single_column : astropy.table.Column
        The input column to stringify
        
    Returns
    -------
    astropy.table.Column
        Stringified version of input column
    """
    new_col = svalv(single_column)
    new_col.meta = single_column.meta
    return new_col

def stringify_table(t):
    """
    Substitutes strings for bytes values in the given table.
    
    Parameters
    ----------
    t : astropy.table.Table
        An astropy table assumed to have been created from a VOTABLE.
    
    Returns
    -------
    astropy.table.Table
        The same table as input, but with bytes-valued cells replaced by strings.
    """
    # This mess will look for columns that should be strings and convert them.
    if (len(t) is 0):
        return   # Nothing to convert
    
    scols = []
    for col in t.columns:
        colobj = t.columns[col]
        if (colobj.dtype == 'object' and isinstance(t[colobj.name][0], bytes)):
            scols.append(colobj.name)

    for colname in scols:
        t[colname] = sval_whole_column(t[colname])
        


class RegistryClass(BaseQuery):
    """
    Registry query class.
"""


    def __init__(self):

        super(RegistryClass, self).__init__()

        self._REGISTRY_TAP_SYNC_URL = conf.registry_tap_url + "/sync"


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
        
        aptable = self._astropy_table_from_votable_response(response)
        
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

    
    def _astropy_table_from_votable_response(self, response):
        """
        Takes a VOTABLE response from a web service and returns an astropy table.
        
        Parameters
        ----------
        response : requests.Response
            Response whose contents are assumed to be a VOTABLE.
            
        Returns
        -------
        astropy.table.Table
            Astropy Table containing the data from the first TABLE in the VOTABLE.
        """
        
        # The astropy table reader would like a file-like object, so convert
        # the response content a byte stream.  This assumes Python 3.x.
        # 
        # (The reader also accepts just a string, but that seems to have two 
        # problems:  It looks for newlines to see if the string is itself a table,
        # and we need to support unicode content.)
        file_like_content = io.BytesIO(response.content)
        
        # The astropy table reader will auto-detect that the content is a VOTABLE
        # and parse it appropriately.
        aptable = Table.read(file_like_content)
        
        # String values in the VOTABLE are stored in the astropy Table as bytes instead 
        # of strings.  To makes accessing them more convenient, we will convert all those
        # bytes values to strings.
        stringify_table(aptable)
        
        return aptable



Registry = RegistryClass()
