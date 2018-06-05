from .image import Image 
from astropy.coordinates import SkyCoord

def test_skycoord():
    from astropy.coordinates import SkyCoord
    pos=SkyCoord.from_name('m82')
    results=Image.query('https://skyview.gsfc.nasa.gov/cgi-bin/vo/sia.pl?survey=swiftuvot&',coords=pos,radius='0.03')
    assert results[0][0]['Ra'] > 148 and results[0][0]['Ra'] < 149

def test_radec():
    results=Image.query('https://skyview.gsfc.nasa.gov/cgi-bin/vo/sia.pl?survey=swiftuvot&',coords='19.,45.7',radius='0.03')
    assert results[0][0]['Ra'] > 19.2 and results[0][0]['Ra'] < 19.3


