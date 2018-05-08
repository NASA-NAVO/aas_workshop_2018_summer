import requests

from .utils import sval, astropy_table_from_votable_response


def sia_query(access_url, ra, dec, size, image_formats='ALL', print_url=False):
    """
        
    Parameters
    ----------
    access_url : str
        The URL endpoint for the SIA service.
    ra : str or number
        The Right Ascension (ICRS degrees) of the central search point
    dec: str or number
        The Declination (ICRS degrees) of the central search point
    size: str or number
        The diameter of the search circle (cone) in degrees
    image_formats: str
        A comma-delimited list of acceptable image MIME types 
        (choices are usually 'image/fits', 'image/jpeg', 'image/png').
        May also choose:
            'ALL' - All formats acceptable (the default)
            'GRAPHIC' - Allows jpeg png and gif
            'METADATA' - Denotes a Metadata Query: no images are requested; only metadata 
            (i.e., SIA result FIELD definitions) should be returned.
    print_url : bool
        Whether or not to print the query URL.  
    
    Returns
    -------
    astropy.table.Table
        An astropy table created from the contents of the VOTABLE response from the SIA query.
    """
    params = {
        'POS': sval(ra) + ',' + sval(dec),
        'SIZE': sval(size),
        'FORMAT': image_formats
    }
    results = requests.get(access_url, params)
    if (print_url):
        print('Queried: ' + results.url)

    aptable = astropy_table_from_votable_response(results)
    return aptable
