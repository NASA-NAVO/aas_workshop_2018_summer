from .image import Image 
from astropy.coordinates import SkyCoord

def test_skycoord():
    results=Image.query('https://skyview.gsfc.nasa.gov/cgi-bin/vo/sia.pl?survey=swiftuvot&',coords='19.,45.7',radius='0.03')
    assert results[0][0]['Ra'] > 19.2 and results[0][0]['Ra'] < 19.3


