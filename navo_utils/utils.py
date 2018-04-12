#
# Imports
#

import requests
import io, re
import numpy as np
from astropy.table import Table, unique
from IPython.core.debugger import Tracer
#
# Support for VOTABLEs as astropy tables
#

def astropy_table_from_votable_response(response):
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

    # TODO: Add error checking here....
    
    # The astropy table reader will auto-detect that the content is a VOTABLE
    # and parse it appropriately.
    aptable = Table.read(file_like_content, format='votable')
    aptable.meta['url']=response.url
    aptable.meta['text']=response.text
    # String values in the VOTABLE are stored in the astropy Table as bytes instead 
    # of strings.  To makes accessing them more convenient, we will convert all those
    # bytes values to strings.
    stringify_table(aptable)
    
    return aptable

def find_column_by_ucd(table, ucd):
    """
    Given an astropy table derived from a VOTABLE, this function returns
    the first Column object that has the given Universal Content Descriptor (UCD).  
    The name field of the returned value contains the column name and can be used 
    for accessing the values in the column.
    
    Parameters
    ----------
    table : astropy.table.Table
        Astropy Table which was created from a VOTABLE (as if by astropy_table_from_votable_response).
    ucd : str
        The UCD identifying the column to be found.
    
    Returns
    -------
    astropy.table.Column
        The first column found which had the given ucd.  None is no such column found.
        
    Example
    -------
    col = find_column_by_ucd(my_table, 'VOX:Image_Title')
    print ('1st row title value is:', my_table[col.name][0])
    """
    
    # Loop through all the columns looking for the UCD
    for key in table.columns:
        col = table.columns[key]
        ucdval = col.meta.get('ucd')
        if (ucdval is not None):
            if (ucd == ucdval):
                return col
    
    return None
#
# Wrappers for Virtual Observatory queries
#

def tap_query(query, tap_service):
    """
    Executes the specified TAP query at the specified TAP service and returns
    the result as an astropy Table.  This function assumes that tap_service is
    a synchronous TAP service URL.
    
    Parameters
    ----------
    query : str
        ADQL (SQL-like) to execute on the given TAP service.
    tap_service : str
        URL endpoint for the desired synchronous TAP service.  This URL will be
        the endpoint for the TAP service identified in the NAVO registry, followed by '/sync'.
    
    Returns
    -------
    astropy.table.Table
        An astropy table created from the contents of the VOTABLE response from the TAP query.
           
    """
    tap_params = {
        "request": "doQuery",
        "lang": "ADQL",
        "query": query
    }
    results = requests.get(tap_service, data=tap_params)
    print('Queried: ' + results.url)

    aptable = astropy_table_from_votable_response(results)
    return aptable


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
        
        


def parse_coords(incoords, **kwargs):
    """Convert whatever the user gives to a simple list of SkyCoord objects.

    Depending on what's given, it calls the appropriate SkyCoord
    constructor. Inputs can be 
    - a single string (comma or space separated; see SkyCoord docs), or 
    - a pair of two strings, i.e., ['ra','dec'], or
    - a list of strings ['ra dec', 'ra dec'] or
    - a list of lists [['ra','dec'],['ra','dec']] or
    - a list of floats [ra,dec], or 
    - a list of lists of floats  [[ra,dec],[ra,dec]] 

    Special cases include a list of two strings. This could be two
    positions, each with an RA+DEC pair specified as a single string,
    or it could be simply the list ['ra','dec']. To decide, look at the
    first to see what format it looks like. Examples include

    ['h m s','h m s'] # one position's RA, DEC in hms
    ['ra.xxx dec.xxx','ra2.xxx dec2.xxx'] # two positions RA, DEC in degrees
    ['ra.xxx','dec.xxx'] # one position's RA, DEC in deg
    ['h:m.m h:m', 'h2:m.m h2:m'] # two position's RA,DEC pairs in h:m.m
    etc.

    """
    from astropy.coordinates import SkyCoord
    from astropy import units as u
    coords=[]
    # First, the incoords must be either a single string or a list. If
    # a list, then each entry in the list must be either a single
    # string that has both (e.g., "RA DEC" or "RA, DEC") or a list of
    # two [RA,DEC] (where RA could be str or float).
    
    # Then worry about the ambiguity of a list of 2:  two positions
    # each in single-string format or one position specified as a
    # pair? If it's the former, then each *has* to have a divider,
    # either white space or comma. But a single RA could have a
    # space. But if it has one, then it should have two.
    #
    #    ['h m s','d m s'] # one position's RA, DEC in hms
    #    ['ra.xxx','dec.xxx'] # one position's RA, DEC in deg
    #    ['h:m.m', 'd:m'] # ??
    #Tracer()()
    if len(incoords) == 2 and type(incoords[0]) is str:
        if re.match("^\s*\S+\s+\S+\s*$" ,incoords[0]):
            # "x y" is always a pair in a stringle string. But only if
            # there's only one whitespace:
            incoords=[ [incoords[0]], [incoords[1]] ]
        elif re.match("^\s*\S+\s+\S+\s+\S+\s*$",incoords[0]):
            # "x y z" is always a single coordinate, so the list is a single pair
            # In this case, change it to a list of lists
            incoords=[ incoords ]
        else:
            # Anything else has to be ra.ddd, HhMmSs, or HhM.Mm or HH:MM.M or something for a single entry
            incoords=[ incoords ]
    # If one gives a list of floats [10.6,41.2], then make a list of lists again
    elif len(incoords)==2 and type(incoords[0]) is float:
        incoords=[ incoords ]
    elif type(incoords) is str:
        incoords=[ [incoords] ]
    elif len(incoords)>2 and type(incoords[0]) is str:
        incoords=[ [s] for s in incoords]
    elif len(incoords)>2 and type(incoords[0]) is list and type(incoords[0][0]) is float or type(incoords[0][0]) is int:
        pass
    else:
        #print("WARNING: I'm confused about the input: {}; passing to SkyCoord()".format(incoords))
        pass
        
    # Now incoords is always a list, and each entry in the list is a position. That position
    # is *also* a list, either of one string or two coordinates. 
    for i,c in enumerate(incoords):
        if type(c[0]) is str and \
           ('h' in c[0] or ':' in c[0] or re.match("^\s*\S+\s+\S+\s+\S+\s*$", c[0])
           or re.match("^\s*\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s*$", c[0])):
            inunit=(u.hourangle,u.deg)
        else:
            inunit='deg'
        if len(c) == 1: 
            coords.append( SkyCoord(c[0],unit=inunit) )
        elif type(c[0]) is str:
            coords.append( SkyCoord(c[0], c[1], unit=inunit ))
        elif type(c[0]) is float or type(c[0]) is int:
            coords.append( SkyCoord(c[0]*u.degree,c[1]*u.degree,unit=inunit) )
        else:
            print("ERROR:  I'm confused about entry {}: {}".format(i,c))
            return None

    return coords

            

