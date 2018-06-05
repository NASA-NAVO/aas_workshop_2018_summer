from .cone import Cone 

def test_skycoord():
    from astropy.coordinates import SkyCoord
    pos=SkyCoord.from_name('m82')
    result_list=Cone.query("https://heasarc.gsfc.nasa.gov/cgi-bin/vo/cone/coneGet.pl?table=rosmaster&",coords=pos,radius=0.5)    
    assert result_list[0][0]['ra'] > 148 and result_list[0][0]['ra'] < 149


def test_radec():
    pos='148.97, 69.68'
    result_list=Cone.query("https://heasarc.gsfc.nasa.gov/cgi-bin/vo/cone/coneGet.pl?table=rosmaster&",coords=pos,radius=0.5)
    assert result_list[0][0]['ra'] > 148.0 and result_list[0][0]['ra'] < 149.0


def test_meta():
    pos='19.0,45.7'
    result_list=Cone.query("https://heasarc.gsfc.nasa.gov/cgi-bin/vo/cone/coneGet.pl?table=foobar&",coords=pos,radius=0.5)
    assert "Unknown table" in result_list[0].meta['text']
