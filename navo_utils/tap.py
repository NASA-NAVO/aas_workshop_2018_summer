# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VO Queries
"""

from __future__ import print_function, division
#from IPython.core.debugger import Tracer
from astroquery.query import BaseQuery
import numpy
from . import utils

__all__ = ['Tap', 'TapClass']

class TapClass(BaseQuery):
    """
    Tap query class.
    """


    def __init__(self):

        super(TapClass, self).__init__()
        self._TIMEOUT = 60 # seconds
        self._RETRIES = 2 # total number of times to try

    def query(self, service, query, upload_file=None,upload_name=None):

        if type(service) is str or numpy.str_:
            service = {"access_url":service}

        url = service['access_url'] + '/sync?'

        tap_params = {
            "request": "doQuery",
            "lang": "ADQL",
            "query": query
        }

        if upload_file is not None:
            if upload_name is None:
                print("ERROR: you have to give a name to use in the query for the uploaded table.")
                return None
            ## Why does neither of these work?
            files={'uplt':open(upload_file,'rb')}
            #files={'uplt':upload_file}
            tap_params['upload'] = upload_name+',param:uplt'
        else:
            files=None

        response = utils.try_query(url, post_data=tap_params, timeout=self._TIMEOUT, retries=self._RETRIES,files=files)

        aptable = utils.astropy_table_from_votable_response(response)
        return aptable

Tap = TapClass()
