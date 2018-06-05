from .spectra import Spectra, SpectraColumn
from astropy.coordinates import SkyCoord


def test_skycoord():
    from astropy.coordinates import SkyCoord
    pos=SkyCoord.from_name('m82')
    results=Spectra.query('https://heasarc.gsfc.nasa.gov/xamin/vo/ssa?table=chanmaster&',coords=pos,radius=0.03)
    assert results[0][0]['ra'] > 148 and results[0][0]['ra'] < 149

def test_radec():
    pos='148.97, 69.68'
    results=Spectra.query('https://heasarc.gsfc.nasa.gov/xamin/vo/ssa?table=chanmaster&',coords=pos,radius='0.03')
    assert results[0][0]['ra'] > 148 and results[0][0]['ra'] < 149.


