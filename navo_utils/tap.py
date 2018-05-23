# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VO Queries
"""

from __future__ import print_function, division
#from IPython.core.debugger import Tracer
from astroquery.query import BaseQuery

from . import utils

__all__ = ['Tap', 'TapClass']

class TapClass(BaseQuery):
    """
    Tap query class.
    """


    def __init__(self):

        super(TapClass, self).__init__()
        self._TIMEOUT = 60 # seconds
        self._RETRIES = 1 # total number of times to try

    def query(self, service, query):

        if type(service) is str:
            service = {"access_url":service}

        url = service['access_url'] + '/sync?'

        tap_params = {
            "request": "doQuery",
            "lang": "ADQL",
            "query": query
        }

        response = utils.try_query(url, post_data=tap_params, timeout=self._TIMEOUT, retries=self._RETRIES)

        aptable = utils.astropy_table_from_votable_response(response)
        return aptable

Tap = TapClass()
