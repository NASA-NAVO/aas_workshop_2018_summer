# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VO Queries
"""

from __future__ import print_function, division
#from IPython.core.debugger import Tracer

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


__all__ = ['Tap', 'TapClass']
    
class TapClass(BaseQuery):
    """
    Tap query class.
    """


    def __init__(self):

        super(TapClass, self).__init__()
        self._TIMEOUT=60 # seconds
        self._RETRIES = 1 # total number of times to try

    def query(self, service, query, verbose=False, **kwargs):
        
        if type(service) is str:
            service={"access_url":service}

        url = service['access_url'] + '/sync?'
        
        tap_params = {
            "request": "doQuery",
            "lang": "ADQL",
            "query": query
        }

        response=utils.try_query(url,post_data=tap_params,timeout=self._TIMEOUT,retries=self._RETRIES)
        
        aptable = utils.astropy_table_from_votable_response(response)        
        return aptable            

Tap = TapClass()
